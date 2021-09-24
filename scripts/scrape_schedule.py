from django.conf import settings
from core import models as m

import requests
from bs4 import BeautifulSoup as bs
import html5lib

from django.utils import timezone
from time import sleep
from datetime import date, datetime, timedelta
from dateutil import parser

import re
from typing import Optional

from . import utils as u

misc_schedule_soups = []
def scrape_from_route(route: m.Route, url: Optional[bool] = None) -> m.Sailing:
    # cal = Calendar()
    # if not route.is_bookable:
        # return ValueError(f'Cannot scrape non-bookable route {route}')
    is_recursive = not url
    sleep(settings.SCRAPER_PAUSE_SECS)
    print('\n')
    req = requests.get(url or
        settings.SCRAPER_SCHEDULE_SEASONAL_URL.format(route.origin.code, route.dest.code))
    req.encoding = req.apparent_encoding
    print(f'got {req.status_code} on {req.url}')
    soup = bs(req.text, 'html5lib')
    tbl = soup.select_one('.table-seasonal-schedule')

    if is_recursive:
        m.Sailing.objects.filter(route=route).delete()
    
    sailing = m.Sailing()
    scheduledSailings = []

    if tbl:
        dateSelections = soup.select_one('select')
        dateRanges = []
        dateRange = None
        for dateOption in dateSelections.select('option'):
            pDateRange = u.from_schedule_date_range(dateOption.getText(strip=True))
            if dateOption.get('selected', 'UNSELECTED') == 'UNSELECTED':
                dateRanges.append(pDateRange)
            else:
                dateRange = pDateRange
        
        if type(dateRange) == type(None):
            dateRange = dateRanges.pop(0)
        
        if is_recursive:
            for otherDateRange in dateRanges:
                dateRangeParam = u.date_range_url_param(otherDateRange)
                scrape_from_route(route, 
                    f'{settings.SCRAPER_SCHEDULE_SEASONAL_URL.format(route.origin.code, route.dest.code)}?departureDate={dateRangeParam}'
                )
        
        print('Date range:', u.pretty_date_range(dateRange))
    
        prevWeekdayName = ''
        for row in tbl.select('tr'):
            weekDay = row.select_one('.text-capitalize')
            if not weekDay:
                print('Skipping row')
                continue
            weekDayName = weekDay.getText(strip=True).upper()
            additionals = row.select_one('.progtrckr')
            if weekDayName:
                hours, mins = additionals.select_one('span').getText(strip=True).upper().split()
                sailing = m.Sailing.objects.create(
                    route = route,
                    duration= timedelta(minutes=int(mins.replace('M', '')), hours=int(hours.replace('H', '')))
                )
            else:
                weekDayName = prevWeekdayName
            
            for i, additional in enumerate(additionals.select('.prog-tracker-entry-seasonal-schedules')):
                classes = additional.get('class', [])
                addText = additional.getText(strip=True).upper()
                if 'stop-over-blank-circle' in classes:
                    m.EnRouteStop.objects.create(
                        sailing = sailing,
                        location = m.Location.objects.get(name__iexact = addText.replace('STOP AT ', '')),
                        is_transfer = False,
                        order = i,
                    )
                elif 'stop-over-line-circle' in classes:
                    m.EnRouteStop.objects.create(
                        sailing = sailing,
                        location = m.Location.objects.get(name__iexact = addText.replace('TRANSFER AT ', '')),
                        is_transfer = True,
                        order = i,
                    )
                
            timeCol = row.select('td')[2]
            # timeSep = '{NEW_TIME}'
            timeStrs = timeCol.find_all(text=True, recursive=False)[0].getText(strip=True).split(',')
            for infoTime in timeCol.select('.schedules-info-time'):
                timeStrs.append(infoTime.getText(strip=True))
            
            for timeStr in timeStrs:
                if not timeStr:
                    continue
                time = u.from_schedule_time(timeStr)
                print('Time:', time.findText)
                skipDates = []
                onlyDates = []
                for span in timeCol.select('.schedules-additional-info'):
                    spanText = span.getText(strip=True).replace('*', '').upper()
                    if spanText.endswith(','):
                        spanText = spanText[:-1]
                    if time.findText in spanText:
                        spanDates = [
                            u.from_schedule_date(dateText)
                            for dateText in spanText.split(':')[-1].strip().split(',')
                        ]
                        if 'ONLY ON:' in spanText:
                            onlyDates.extend(spanDates)
                        elif 'NOT AVAILABLE ON:' in spanText:
                            skipDates.extend(spanDates)
                if onlyDates: print('Only:', *onlyDates)
                if skipDates: print('Skip:', *skipDates)

                if onlyDates:
                    insertCount = 0
                    for lDate in dateRange:
                        if not u.schedule_includes(onlyDates, lDate):
                            continue
                        insertCount += 1
                        scheduledSailings.append(m.ScheduledSailing(
                            sailing = sailing,
                            time = datetime(
                                year = lDate.year,
                                month = lDate.month,
                                day = lDate.day,
                                hour = time.hour,
                                minute = time.minute,
                                tzinfo = timezone.get_current_timezone()
                            )
                        ))
                    if insertCount: print('Inserted', insertCount)
                else:
                    skipCount = 0
                    for lDate in dateRange:
                        if u.schedule_includes(skipDates, lDate):
                            skipCount += 1
                            continue
                        scheduledSailings.append(m.ScheduledSailing(
                            sailing = sailing,
                            time = datetime(
                                year = lDate.year,
                                month = lDate.month,
                                day = lDate.day,
                                hour = time.hour,
                                minute = time.minute,
                                tzinfo = timezone.get_current_timezone()
                            )
                        ))
                    if skipCount: print('Skipped', skipCount)
            prevWeekdayName = weekDayName

    else:
        print('Could not retrieve schedule table for', route)
        if not is_recursive:
            return
        
        for miscSoup in misc_schedule_soups:
            print('Trying misc schedule page')
            mainElem = miscSoup.select_one(f'#{route.origin.code}-{route.dest.code}')
            if not mainElem:
                print('Could not find alternate timetable')
                continue

            allDiv = mainElem.find_parent('div')
            dateTitles = allDiv.select('.accordion-title')
            timeTables = allDiv.select('tbody')
            if len(dateTitles) != len(timeTables):
                raise ValueError(f'found {len(dateTitles)} date titles but {len(timeTables)} schedules')
            for i, dateTitle in enumerate(dateTitles):
                dateRange = u.from_schedule_date_range(dateTitle.getText(strip=True))
                print('Date range:', u.pretty_date_range(dateRange))
                table = timeTables[i]
                rows = table.select('tr')
                NOTES_SEPARATOR = '{BLINGUS}'
                notes = [
                    noteText.strip().upper()
                    for noteText in rows[-1].getText(strip=True, separator=NOTES_SEPARATOR).split(NOTES_SEPARATOR)
                ]
                for row in rows[:-1]:
                    cols = row.select('td')
                    if len(cols) != 4:
                        print('Skipping row, found', cols, 'cols')
                        continue
                    leaveText, daysText, stopsText, arriveText = [
                        col.getText(strip=True)
                        for col in cols
                    ]
                    days = []
                    for dayText in daysText.split(','):
                        dayText = dayText.strip().replace('*', '').upper()
                        if '-' in dayText:
                            startDay, endDay = dayText.split('-')
                            days.extend([
                                singleDay
                                for singleDay in range(u.month_from_text(startDay), u.month_from_text(endDay) + 1)
                            ])
                        else:
                            days.append(u.month_from_text(dayText))
 
                    leaveTime = u.from_schedule_time(leaveText)
                    arriveTime = u.from_schedule_time(arriveText)
                    
                    time = u.from_schedule_time(leaveText)
                    print('Time:', time.findText)
                    sailing = m.Sailing.objects.create(
                        route = route,
                        duration = timedelta(
                            hours = arriveTime.hour - leaveTime.hour,
                            minutes = arriveTime.minute - leaveTime.minute,
                        ),
                    )
                    for i, stopText in enumerate(stopsText.split(',')):
                        stopText = stopText.strip().upper()
                        if 'TRANSFER' in stopText:
                            m.EnRouteStop.objects.create(
                                sailing = sailing,
                                location = m.Location.objects.get(
                                    name__icontains = stopText.replace('TRANSFER AT ', '').replace('TRANSFER ', '')
                                ),
                                is_transfer = True,
                                order = i,
                            )
                        else:
                            m.EnRouteStop.objects.create(
                                sailing = sailing,
                                location = m.Location.objects.get(name__icontains = stopText),
                                is_transfer = True,
                                order = i,
                            )

                    skipDates = []
                    onlyDates = []
                    for noteText in notes:
                        if noteText.endswith(','):
                            noteText = noteText[:-1]
                        if time.findText in noteText:
                            # unfortunately the formatting on the website is not standardized here
                            # use regex & fuzzy parsing to identify dates
                            spanDates = [
                                parser.parse(dateText.strip().upper(),
                                    tzinfo = timezone.get_current_timezone(),
                                    fuzzy = True,
                                ).date()
                                for dateText in u.multi_split(
                                    noteText.split(':')[-1].strip(),
                                    {str(t.year) for t in dateRange}
                                )
                            ]
                            if 'ONLY ON:' in noteText:
                                onlyDates.extend(spanDates)
                            elif 'EXCEPT ON:' in noteText:
                                skipDates.extend(spanDates)
                    if onlyDates: print('Only:', *onlyDates)
                    if skipDates: print('Skip:', *skipDates)
                    
                    if onlyDates:
                        insertCount = 0
                        for lDate in dateRange:
                            if not u.schedule_includes(onlyDates, lDate):
                                continue
                            insertCount += 1
                            scheduledSailings.append(m.ScheduledSailing(
                                sailing = sailing,
                                time = datetime(
                                    year = lDate.year,
                                    month = lDate.month,
                                    day = lDate.day,
                                    hour = time.hour,
                                    minute = time.minute,
                                    tzinfo = timezone.get_current_timezone()
                                )
                            ))
                        if insertCount: print('Inserted', insertCount)
                    else:
                        skipCount = 0
                        for lDate in dateRange:
                            if u.schedule_includes(skipDates, lDate):
                                skipCount += 1
                                continue
                            scheduledSailings.append(m.ScheduledSailing(
                                sailing = sailing,
                                time = datetime(
                                    year = lDate.year,
                                    month = lDate.month,
                                    day = lDate.day,
                                    hour = time.hour,
                                    minute = time.minute,
                                    tzinfo = timezone.get_current_timezone()
                                )
                            ))
                        if skipCount: print('Skipped', skipCount)
            break
    
    m.ScheduledSailing.objects.bulk_create(scheduledSailings)
    return sailing


def run():
    global misc_schedule_soups
    for url in settings.SCRAPER_MISC_SCHEDULE_URLS:
        sleep(settings.SCRAPER_PAUSE_SECS)
        req = requests.get(url)
        req.encoding = req.apparent_encoding
        print('Adding misc table', url)
        print(f'got {req.status_code} on {req.url}')
        misc_schedule_soups.append(bs(req.text, 'html5lib'))

    for route in m.Route.objects.all(): #filter(is_bookable=True):
        scrape_from_route(route)
