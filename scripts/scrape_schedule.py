from django.conf import settings
import core.models as m

from bs4 import BeautifulSoup as bs
import html5lib
# import ujson

from django.utils import timezone
from datetime import datetime, timedelta
from calendar import Calendar, month_abbr

import pandas as pd

import requests
# from urllib.parse import urlparse
from time import sleep

from dataclasses import dataclass

dateList = pd.date_range(datetime.today(),
    periods = settings.SCRAPER_SCHEDULE_DATE_PERIODS,
    freq = '1D',
    tz = timezone.get_current_timezone()
).tolist()

@dataclass
class ScrapedSchedule:
    findText: str

    def __str__(self) -> str:
        return self.findText

@dataclass
class ScheduleTime(ScrapedSchedule):
    hour: int
    minute: int

@dataclass
class ScheduleDate(ScrapedSchedule):
    day: int
    month: int

def scheduleIncludes(schedule: list, search) -> bool:
    for d in schedule:
        if d.day == search.day and d.month == search.month:
            return True
    return False

def fromScheduleTime(schedule: str) -> ScheduleTime:
    findText = schedule.replace('*', '').replace(',', '').strip().upper()
    splitText = findText.split()
    hour, minute = splitText[0].split(':')
    hour = int(hour) -1
    minute = int(minute)
    if splitText[1] == 'PM':
        hour += 12
    return ScheduleTime(findText, hour, minute)

def fromScheduleDate(schedule: str) -> ScheduleDate:
    findText = schedule.replace('*', '').replace(',', '').strip().upper()
    splitText = findText.split()
    day = int(splitText[0])
    month = -1
    for i, abbr in enumerate(month_abbr):
        if abbr.upper() == splitText[1]:
            month = i + 1
            break
    return ScheduleDate(findText, day, month)


def service(name: str, is_additional: bool) -> m.Service:
    amenity, created = m.Service.objects.get_or_create(name=name, is_additional=is_additional)
    if created:
        print('Created service', amenity)
    return amenity


def scrape_from_route(route: m.Route) -> m.Sailing:
    # cal = Calendar()
    if not route.is_bookable:
        return ValueError(f'Cannot scrape non-bookable route {route}')
    
    sleep(settings.SCRAPER_PAUSE_SECS)
    req = requests.get(settings.SCRAPER_SCHEDULE_SEASONAL_URL.format(route.origin.code, route.dest.code))
    req.encoding = req.apparent_encoding
    print(req.status_code, 'on', req.url)
    soup = bs(req.text ,'html5lib')
    tbl = soup.select_one('.table-seasonal-schedule')
    if not tbl:
        print('Could not retrieve schedule table for', route)
        return

    prevWeekdayName = ''
    m.Sailing.objects.filter(route=route).delete()
    sailing = m.Sailing()
    scheduledSailings = []

    for row in tbl.select('tr'):
        weekDay = row.select_one('.text-capitalize')
        if not weekDay:
            print('Skipping row')
            continue
        weekDayName = weekDay.getText(strip=True).upper()
        additionals = row.select_one('.progtrckr')
        if weekDayName:
            hours, mins = additionals.select_one('span').getText(strip=True).split()
            sailing = m.Sailing.objects.create(
                route = route,
                duration= timedelta(minutes=int(mins.replace('m', '')), hours=int(hours.replace('h', '')))
            )
        else:
            weekDayName = prevWeekdayName
        
        for i, additional in enumerate(additionals.select('.prog-tracker-entry-seasonal-schedules')):
            classes = additional.get('class', [])
            if 'stop-over-blank-circle' in classes:
                locName = additional.getText(strip=True).replace('Stop at ', '')
                m.EnRouteStop.objects.create(
                    sailing = sailing,
                    location = m.Location.objects.get(name = locName),
                    is_transfer = False,
                    order = i,
                )
            elif 'stop-over-line-circle' in classes:
                locName = additional.getText(strip=True).replace('Transfer at ', '')
                m.EnRouteStop.objects.create(
                    sailing = sailing,
                    location = m.Location.objects.get(name = locName),
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
            time = fromScheduleTime(timeStr)
            print('Time:', time.findText)
            skipDates = []
            onlyDates = []
            for span in timeCol.select('.schedules-additional-info'):
                spanText = span.getText(strip=True).replace('*', '').upper()
                if spanText.endswith(','):
                    spanText = spanText[:-1]
                if time.findText in spanText:
                    spanDates = [fromScheduleDate(dateText)
                        for dateText in spanText.split(':')[-1].strip().split(',')
                    ]
                    if 'ONLY ON:' in spanText:
                        onlyDates.extend(spanDates)
                    elif 'NOT AVAILABLE ON:' in spanText:
                        skipDates.extend(spanDates)
            print('Only:', *onlyDates)
            print('Skip:', *skipDates)

            if onlyDates:
                for lDate in dateList:
                    if not scheduleIncludes(onlyDates, lDate): continue
                    print('Inserting one')
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
            else:
                for lDate in dateList:
                    if scheduleIncludes(skipDates, lDate):
                        print('Skipping one')
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
        prevWeekdayName = weekDayName
    m.ScheduledSailing.objects.bulk_create(scheduledSailings)
    return sailing


def run():
    for route in m.Route.objects.filter(is_bookable=True):
        scrape_from_route(route)
        print('\n')
