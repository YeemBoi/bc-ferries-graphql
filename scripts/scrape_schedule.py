from django.conf import settings
from django.utils import timezone
from core import models as m

from datetime import date, datetime, timedelta
from calendar import day_name, day_abbr
from dateutil import parser
import pandas as pd

import re
from typing import Optional, NamedTuple, Generator
from bs4 import BeautifulSoup as bs
from common import scraper_utils as u

misc_schedule_soups: list[bs] = []

def date_range_url_param(date_range: pd.DatetimeIndex) -> str:
        return '-'.join([dateVal.strftime('%Y%m%d')
            for dateVal in [date_range[0], date_range[-1]]])


def make_scheduled_sailings(
    sailing: m.Sailing,
    time,
    date_range: pd.DatetimeIndex,
    skip: list,
    only: list,
    week_days: set[int],
    ) -> Generator[m.ScheduledSailing, None, None]:

    print(f"Time: {time} - Days: {', '.join([day_abbr[i] for i in week_days])}")
    u.soft_print_iter('Only:', only)
    u.soft_print_iter('Skip:', skip)

    if only:
        insert_count = 0
        for l_date in date_range:
            if not u.schedule_includes(only, l_date):
                continue
            insert_count += 1
            yield m.ScheduledSailing(
                sailing = sailing,
                time = datetime(
                    year = l_date.year,
                    month = l_date.month,
                    day = l_date.day,
                    hour = time.hour,
                    minute = time.minute,
                    tzinfo = timezone.get_current_timezone()
                )
            )
        u.soft_print('Inserted', insert_count)
    else:
        skip_count = 0
        for l_date in date_range:
            if l_date.day_of_week not in week_days:
                continue
            if u.schedule_includes(skip, l_date):
                skip_count += 1
                continue
            yield m.ScheduledSailing(
                sailing = sailing,
                time = datetime(
                    year = l_date.year,
                    month = l_date.month,
                    day = l_date.day,
                    hour = time.hour,
                    minute = time.minute,
                    tzinfo = timezone.get_current_timezone()
                )
            )
        u.soft_print('Skipped', skip_count)


def parse_noted_dates(note_text: str, date_range: pd.DatetimeIndex) -> Generator[date, None, None]:
    # unfortunately the formatting on the misc timetables is not standardized
    # use regex & fuzzy parsing to identify dates
    for date_text in u.multi_split(
        u.multi_split(
            note_text.split('HOLIDAY MONDAY')[0].strip(), [':', ' ON ']
                )[-1].strip(),
            [',', '&', ' AND ', *{str(t.year) for t in date_range}]
        ):
        if len(date_text.strip()) > 5:
            yield parser.parse(
                f"{date_text.strip().upper()} {timezone.get_current_timezone_name()}",
                fuzzy = True,
            ).date()

class LocationCertainty(NamedTuple):
    terminal: m.Terminal
    is_certain: bool

def get_terminal(name: str) -> LocationCertainty:
    print('Getting en-route stop:', name)
    terminals = m.Terminal.objects.filter(name__icontains = name)
    return LocationCertainty(terminals.first(), terminals.count() == 1)


def scrape_route(route: m.Route, url: Optional[str] = None) -> m.Sailing:
    is_recursive = not url
    if is_recursive:
        url = settings.SCRAPER_SCHEDULE_SEASONAL_URL.format(route.scraper_url_param())
    soup = u.request_soup(url)
    tbl = soup.select_one('.table-seasonal-schedule')

    if is_recursive:
        m.Sailing.objects.filter(route=route).delete()
    
    sailing = m.Sailing()
    scheduled_sailings = []
    en_route_stops = []

    if tbl:
        date_selections = soup.select_one('select')
        date_ranges = []
        date_range = None
        for date_option in date_selections.select('option'):
            p_date_range = u.from_schedule_date_range(date_option.get_text(strip=True), '%b %d, %Y')
            if date_option.get('selected', 'UNSELECTED') == 'UNSELECTED':
                date_ranges.append(p_date_range)
            else:
                date_range = p_date_range
        
        if type(date_range) == type(None):
            date_range = date_ranges.pop(0)
        
        if is_recursive:
            for other_date_range in date_ranges:
                scrape_route(route, f"{url}?departure_date={date_range_url_param(other_date_range)}")
        
        print('Date range:', u.pretty_date_range(date_range))
    
        prev_week_day_name = ''
        is_short_format = False
        for row in tbl.select_one('tbody').select('tr'):
            week_day_name = ''
            cols = row.select('td')
            if week_day := row.select_one('.text-capitalize'):
                week_day_name = week_day.get_text(strip=True).upper()
                is_short_format = False
            else:
                if (potential_week_day := cols[1].get_text(strip=True).split()[0].strip().title())\
                    in day_name:
                    if not is_short_format: # Only print once
                        print('Parsing shortened schedule format')
                    is_short_format = True
                    week_day_name = potential_week_day[:3].upper()
                else: 
                    print(f'Skipping row - found "{potential_week_day}"')
                    continue
                
            additionals = row.select_one('.progtrckr')
            if week_day_name:
                hours, mins = additionals.select_one('span').get_text(strip=True).upper().split()
                sailing = m.Sailing.objects.create(
                    route = route,
                    official_page = url,
                    duration = timedelta(minutes=int(mins.replace('M', '')), hours=int(hours.replace('H', '')))
                )
            else:
                week_day_name = prev_week_day_name
            
            for i, additional in enumerate(additionals.select('.prog-tracker-entry-seasonal-schedules')):
                classes = additional.get('class', [])
                add_text = additional.get_text(strip=True).upper()
                if 'stop-over-blank-circle' in classes:
                    terminal, is_certain = get_terminal(add_text.replace('STOP AT ', ''))
                    en_route_stops.append(m.EnRouteStop(
                        sailing = sailing,
                        terminal = terminal,
                        is_certain = is_certain,
                        is_transfer = False,
                        order = i,
                    ))
                elif 'stop-over-line-circle' in classes:
                    terminal, is_certain = get_terminal(add_text.replace('TRANSFER AT ', ''))
                    en_route_stops.append(m.EnRouteStop(
                        sailing = sailing,
                        terminal = terminal,
                        is_certain = is_certain,
                        is_transfer = True,
                        order = i,
                    ))
                
            time_col = cols[2]
            time_strs = time_col.find_all(text=True, recursive=False)[0].get_text(strip=True).split(',')
            for info_time in time_col.select('.schedules-info-time'):
                time_strs.append(info_time.get_text(strip=True))
            note_texts = []
            if is_short_format:
                if note := ' '.join(cols[1].get_text(strip=True).split()[1:]).upper():
                    note_texts.append(note)
            else:
                for info_time in time_col.select('.schedules-additional-info'):
                    info_text = info_time.get_text(strip=True).replace('*', '').upper()
                    if len(info_text) < 10: # eg: 12:00 PM*
                        time_strs.append(info_text)
                    else:
                        note_texts.append(info_text)
            
            for time_str in time_strs:
                if not time_str:
                    continue
                time = u.from_schedule_time(time_str)
                skip_dates = []
                only_dates = []
                for note_text in note_texts:
                    if note_text.endswith(','):
                        note_text = note_text[:-1]
                    if is_short_format or (time.find_text in note_text):
                        span_dates = [
                            u.from_schedule_date(date_text)
                            for date_text in note_text.split(':')[-1].strip().split(',')
                        ]
                        if 'ONLY ON:' in note_text:
                            only_dates.extend(span_dates)
                        elif 'NOT AVAILABLE ON:' in note_text:
                            skip_dates.extend(span_dates)
                scheduled_sailings.extend(make_scheduled_sailings(
                    sailing = sailing,
                    time = time,
                    date_range = date_range,
                    skip = skip_dates,
                    only = only_dates,
                    week_days = {u.day_from_text(week_day_name)},
                ))
            prev_week_day_name = week_day_name
    

    ########  USE ALTERNATIVE SCHEDULES  ########
    else:
        print('Could not retrieve schedule table for', route)
        if not is_recursive:
            return
        
        for misc_soup in misc_schedule_soups:
            print('Trying misc schedule page')
            main_elem = misc_soup.select_one('#' + route.scraper_url_param())
            if not main_elem:
                print('Could not find alternate timetable')
                continue

            allDiv = main_elem.find_parent('div')
            date_titles = allDiv.select('.accordion-title')
            time_tables = allDiv.select('tbody')
            if unmatched_schedule_dates := len(date_titles) != len(time_tables):
                print(f"Found {len(date_titles)} date titles but {len(time_tables)} schedules")
                print("Using fallback dates")
            for i, time_table in enumerate(time_tables):
                date_range = u.from_schedule_date_range(date_titles[i].get_text(strip=True), '%B %d, %Y')\
                    if not unmatched_schedule_dates else u.fallback_dates
                
                print('Date range:', u.pretty_date_range(date_range))
                rows = time_table.select('tr')
                NOTES_SEPARATOR = '{BLINGUS}'
                notes = [
                    note_text.strip().upper()
                    for note_text in rows[-1].get_text(strip=True, separator=NOTES_SEPARATOR).split(NOTES_SEPARATOR)
                ]
                if len(rows[-1].select('td')) == 4:
                    notes = []
                
                for row in rows:
                    cols = row.select('td')
                    if len(cols) != 4:
                        print('Skipping row, found', len(cols), 'cols')
                        continue
                    if not len(row.get_text(strip=True)):
                        print('Skipping blank row')
                        continue
                    leave_text, days_text, stops_text, arrive_text = [
                        col.get_text(strip=True)
                        for col in cols
                    ]
                    leave_time = u.from_schedule_time(leave_text)
                    arrive_time = u.from_schedule_time(arrive_text)
                    days = set()

                    note_indicator = ''
                    holiday_mondays = False
                    for c in range(1,4):
                        if (indicator := '*' * c) in days_text:
                            note_indicator = indicator
                    
                    for day_text in days_text.split(','):
                        day_text = day_text.strip().replace('*', '').upper()
                        if '-' in day_text:
                            startDay, endDay = day_text.split('-')
                            days.update(range(u.day_from_text(startDay), u.day_from_text(endDay) + 1))
                        else:
                            try:
                                if day_text.startswith('HOL '):
                                    holiday_mondays = True
                                days.add(u.day_from_text(day_text.replace('HOL ', '')))
                            except ValueError as e:
                                print(e)
                                print('Trying to select individual dates...')
                                month = 0
                                skipped_tokens = []
                                for token in days_text.replace(',', '').split():
                                    try:
                                        month = u.month_from_text(token)
                                    except ValueError:
                                        try:
                                            sketchyDate = u.ScheduleDate(days_text, int(token), month)
                                            print('Parsed date from', sketchyDate)
                                            only_dates.append(sketchyDate)
                                        except ValueError:
                                            skipped_tokens.append(token)
                                u.soft_print_iter('Skipped tokens:', skipped_tokens)
                                break
                    
                    sailing = m.Sailing.objects.create(
                        route = route,
                        official_page = url,
                        duration = timedelta(
                            hours = arrive_time.hour - leave_time.hour,
                            minutes = arrive_time.minute - leave_time.minute,
                        ),
                    )
                    skip_dates = []
                    only_dates = []
                    for i, stop_text in enumerate(stops_text.split(',')):
                        stop_text = stop_text.strip().upper()
                        if stop_text == 'NON-STOP':
                            continue
                        if 'TRANSFER' in stop_text:
                            terminal, is_certain = get_terminal(stop_text.replace('TRANSFER AT ', '').replace('TRANSFER ', ''))
                            en_route_stops.append(m.EnRouteStop(
                                sailing = sailing,
                                terminal = terminal,
                                is_certain = is_certain,
                                is_transfer = True,
                                order = i,
                            ))
                        else:
                            terminal, is_certain = get_terminal(stop_text)
                            en_route_stops.append(m.EnRouteStop(
                                sailing = sailing,
                                terminal = terminal,
                                is_certain = is_certain,
                                is_transfer = False,
                                order = i,
                            ))

                    for note_text in notes:
                        if len(note_indicator) and note_indicator in note_text:
                            if 'ONLY ON' in note_text:
                                only_dates.extend(parse_noted_dates(note_text, date_range))
                            elif 'EXCEPT ON' in note_text:
                                skip_dates.extend(parse_noted_dates(note_text, date_range))
                        if (not holiday_mondays) and 'HOLIDAY MONDAY' in note_text:
                            skip_dates.extend(parse_noted_dates(note_text, date_range))

                    scheduled_sailings.extend(make_scheduled_sailings(
                        sailing = sailing,
                        time = leave_time,
                        date_range = date_range,
                        skip = skip_dates,
                        only = only_dates,
                        week_days = days,
                    ))
            break

    m.EnRouteStop.objects.bulk_create(en_route_stops)
    m.ScheduledSailing.objects.bulk_create(scheduled_sailings)
    return sailing

def init_misc_schedules():
    global misc_schedule_soups
    for url in settings.SCRAPER_MISC_SCHEDULE_URLS:
        print('Adding misc table', url)
        misc_schedule_soups.append(u.request_soup(url))

def run():
    init_misc_schedules()
    for route in m.Route.objects.all(): # filter(is_bookable=True):
        scrape_route(route)
