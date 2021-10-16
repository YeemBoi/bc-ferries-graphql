from django.utils import timezone
from ferries import models as m

from datetime import date, datetime, timedelta
from calendar import day_name, day_abbr
from dateutil import parser
import pandas as pd

import re
from typing import Optional, NamedTuple, Generator
from bs4 import BeautifulSoup as bs
from common import scraper_utils as u
import logging
log: u.Logger = logging.getLogger(__name__)

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

    log.debug(f"Time: {time} - Days: {', '.join([day_abbr[i] for i in week_days])}")
    log.soft_print_iter('Only:', only)
    log.soft_print_iter('Skip:', skip)

    if only:
        insert_count = 0
        for l_date in date_range:
            if not u.schedule_includes(only, l_date):
                continue
            insert_count += 1
            yield m.ScheduledSailing(sailing=sailing, time=u.date_time_combine(l_date, time))
        log.soft_print('Inserted', insert_count)
    else:
        skip_count = 0
        for l_date in date_range:
            if l_date.day_of_week not in week_days:
                continue
            if u.schedule_includes(skip, l_date):
                skip_count += 1
                continue
            yield m.ScheduledSailing(sailing=sailing, time=u.date_time_combine(l_date, time))
        log.soft_print('Skipped', skip_count)


def parse_noted_dates(note_text: str, date_range: pd.DatetimeIndex) -> Generator[date, None, None]:
    # unfortunately the formatting on the misc timetables is not standardized
    # use regex & fuzzy parsing to identify dates
    for date_text in u.multi_split(
        u.multi_split(
            note_text.split('HOLIDAY MONDAY')[0].strip(), [':', ' ON '])[-1].strip(),
            map(re.escape, [',', '&', ' AND ', *{str(t.year) for t in date_range}])
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
    log.debug(f"Getting en-route stop: {name}")
    terminals = m.Terminal.objects.filter(name__icontains = name)
    return LocationCertainty(terminals.first(), terminals.count() == 1)

_alt_note_indicator = re.compile(r'\*+')

def scrape_route(route: m.Route, url: Optional[str] = None) -> m.Sailing:
    is_recursive = not url
    if is_recursive:
        time_initiated = timezone.now()
        url = u.get_url('SCHEDULE_SEASONAL').format(route.scraper_url_param())
    soup = log.request_soup(url)
    tbl = soup.select_one('.table-seasonal-schedule')
    
    sailing = m.Sailing()
    scheduled_sailings = []
    en_route_stops = []

    if tbl:
        date_selections = soup.find('select')
        date_ranges = []
        date_range = None
        for date_option in date_selections.select('option'):
            p_date_range = u.from_schedule_date_range(log, date_option.get_text(strip=True), '%b %d, %Y')
            if date_option.get('selected', 'UNSELECTED') == 'UNSELECTED':
                date_ranges.append(p_date_range)
            else:
                date_range = p_date_range
        if date_range == None: date_range = date_ranges.pop(0)
        
        if is_recursive:
            for other_date_range in date_ranges:
                scrape_route(route, f"{url}?departure_date={date_range_url_param(other_date_range)}")
        
        log.debug(f"Date range: {u.pretty_date_range(date_range)}")
    
        prev_week_day_name = ''
        is_short_format = False
        for row in tbl.find('tbody').select('tr'):
            week_day_name = ''
            cols = row.select('td')
            second_text = u.clean_tag_text(cols[1])
            if week_day := row.select_one('.text-capitalize'):
                week_day_name = u.clean_tag_text(week_day)
                is_short_format = False
            else:
                if (potential_week_day := second_text.split()[0].strip().title())\
                    in day_name:
                    if not is_short_format: # Only print once
                        log.info('Parsing shortened schedule format')
                    is_short_format = True
                    week_day_name = potential_week_day[:3]
                else: 
                    log.info(f'Skipping row - found "{potential_week_day}"')
                    continue
                
            additionals = row.select_one('.progtrckr')
            if week_day_name:
                hours, mins = u.clean_tag_text(additionals.find('span')).split()
                sailing = m.Sailing.objects.create(
                    route = route,
                    official_page = url,
                    duration = timedelta(minutes=int(mins.replace('M', '')), hours=int(hours.replace('H', '')))
                )
            else: week_day_name = prev_week_day_name
            
            for i, additional in enumerate(additionals.select('.prog-tracker-entry-seasonal-schedules')):
                classes = additional.get('class', [])
                add_text = u.clean_tag_text(additional)
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
            time_strs = u.clean_tag_text(time_col.find_all(text=True, recursive=False)[0]).split(',')
            for info_time in time_col.select('.schedules-info-time'):
                time_strs.append(u.clean_tag_text(info_time))
            note_texts = []
            if is_short_format:
                if note := ' '.join(second_text.split()[1:]):
                    note_texts.append(note)
            else:
                for info_time in time_col.select('.schedules-additional-info'):
                    info_text = u.clean_tag_text(info_time).replace('*', '')
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
                        span_dates = map(u.from_schedule_date, note_text.split(':')[-1].strip().split(','))
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
        log.info(f"Could not retrieve schedule table for {route}")
        if not is_recursive:
            return
        
        for misc_soup in misc_schedule_soups:
            log.info('Trying misc schedule page')
            main_elem = misc_soup.select_one('#' + route.scraper_url_param())
            if not main_elem:
                log.info('Could not find alternate timetable')
                continue

            allDiv = main_elem.find_parent('div')
            date_titles = allDiv.select('.accordion-title')
            time_tables = allDiv.select('tbody')
            if unmatched_schedule_dates := len(date_titles) != len(time_tables):
                log.warning(f"Found {len(date_titles)} date titles but {len(time_tables)} schedules")
                log.warning("Using fallback dates")
            for i, time_table in enumerate(time_tables):
                date_range = u.from_schedule_date_range(log, date_titles[i].get_text(strip=True), '%B %d, %Y')\
                    if not unmatched_schedule_dates else u.fallback_dates
                
                log.info(f"Date range: {u.pretty_date_range(date_range)}")
                rows = time_table.select('tr')
                if len(rows[-1].select('td')) == 4:
                    notes = []
                else:
                    NOTES_SEPARATOR = '{BLINGUS}'
                    notes = u.clean_tag_text(rows[-1], True, separator=NOTES_SEPARATOR).split(NOTES_SEPARATOR)
                for row in rows:
                    cols = list(map(u.clean_tag_text, row.select('td')))
                    if len(cols) != 4:
                        log.info(f"Skipping row, found {len(cols)} cols")
                        continue
                    if not len(row.get_text(strip=True)):
                        log.info('Skipping blank row')
                        continue
                    leave_text, days_text, stops_text, arrive_text = cols
                    leave_time = u.from_schedule_time(leave_text)
                    arrive_time = u.from_schedule_time(arrive_text)
                    days = set()

                    note_indicator = ''
                    holiday_mondays = False
                    if indicator := _alt_note_indicator.search(days_text):
                        note_indicator = indicator.group()
                    
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
                                log.info("Could not parse day", exc_info=e)
                                log.info("Trying to select individual dates...")
                                month = 0
                                skipped_tokens = []
                                for token in days_text.replace(',', '').split():
                                    try:
                                        month = u.month_from_text(token)
                                    except ValueError:
                                        try:
                                            sketchyDate = u.ScheduleDate(days_text, int(token), month)
                                            log.info(f"Parsed date from {sketchyDate}")
                                            only_dates.append(sketchyDate)
                                        except ValueError:
                                            skipped_tokens.append(token)
                                log.soft_print_iter('Skipped tokens:', skipped_tokens)
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
                        stop_text = stop_text.strip()
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
                        if note_indicator and note_indicator == _alt_note_indicator.match(note_indicator).group():
                            if 'ONLY ON' in note_text and '#' not in note_text:
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
    if is_recursive:
        m.Sailing.objects.filter(
            route = route,
            fetched_time__lt = time_initiated - timedelta(minutes=1)
        ).delete()
    return sailing

def init_misc_schedules():
    global misc_schedule_soups
    misc_schedule_soups = list(map(log.request_soup, u.get_url('MISC_SCHEDULES')))

def run():
    init_misc_schedules()
    for route in m.Route.objects.all(): # filter(is_bookable=True):
        scrape_route(route)
