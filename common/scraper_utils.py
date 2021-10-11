from django.conf import settings
from django.utils import timezone
from datetime import datetime
from calendar import month_abbr, day_abbr
import pandas as pd
from dataclasses import dataclass

import re
import requests
from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from time import sleep

fallback_dates = pd.date_range(
    start = datetime.now(),
    periods = settings.SCRAPER['FALLBACK_DAY_PERIODS'],
    freq = '1D',
    tz = timezone.get_current_timezone(),
)

def clean(text: str) -> str:
    return text.strip().upper()

def clean_tag_text(tag: Tag, preserve_newlines: bool = False, **kwargs) -> str:
    text = tag.get_text(strip=True, **kwargs)
    if preserve_newlines:
        return clean('\n'.join([
            ' '.join(line.split())
            for line in text.split('\n')
        ]))
    return ' '.join(text.split()).upper()

def schedule_clean(text: str) -> str:
    return text.replace('*', '').replace(',', '')

def multi_split(main_str: str, delimiters) -> list[str]:
    return re.split('|'.join(set(delimiters)), main_str)

def soft_print(pre: str, val):
    if val: print(pre, val)

def soft_print_iter(pre: str, vals):
    if len(vals): print(pre, ', '.join(map(str, vals)))

def date_time_combine(date_val, time_val) -> datetime:
    return datetime(
        year = date_val.year,
        month = date_val.month,
        day = date_val.day,
        hour = time_val.hour,
        minute = time_val.minute,
        tzinfo = timezone.get_current_timezone(),
    )

def _calendar_abbr_to_int(text: str, abbrs: list[str]) -> int:
    cleanedText = clean(text)
    for i, abbr in enumerate(abbrs):
        if abbr.upper() == cleanedText:
            return i
    raise ValueError(f'cannot parse calendar abbreviation from {text}')

def month_from_text(text: str) -> int:
    return _calendar_abbr_to_int(text, month_abbr)

def day_from_text(text: str) -> int:
    return _calendar_abbr_to_int(text, day_abbr)

def pretty_date_range(date_range: pd.DatetimeIndex) -> str:
    return f'{date_range[0].strftime("%x")} - {date_range[-1].strftime("%x")}'

@dataclass
class ScrapedSchedule:
    find_text: str
    def __str__(self) -> str:
        return self.find_text
   
@dataclass
class ScheduleTime(ScrapedSchedule):
    hour: int
    minute: int

@dataclass
class ScheduleDate(ScrapedSchedule):
    day: int
    month: int

def schedule_includes(search_schedule, search_date) -> bool:
    for scheduled_date in search_schedule:
        if scheduled_date.day == search_date.day and scheduled_date.month == search_date.month:
            return True
    return False

def from_schedule_time(schedule: str) -> ScheduleTime:
    schedule = schedule_clean(schedule)
    split_text = schedule.split()
    hour, minute = split_text[0].split(':')
    hour = int(hour) -1
    if minute.endswith('M'): # eg "6:00PM"
        split_text.append(minute[-2:])
        minute = minute[:-2]
    minute = int(minute)
    if (split_text[1] == 'PM' and hour != 12) or (hour == 12 and split_text[1] == 'AM'):
        hour += 12
    return ScheduleTime(schedule, hour, minute)

def from_schedule_date(schedule: str) -> ScheduleDate:
    schedule = schedule_clean(schedule)
    split_text = schedule.split()
    day = int(split_text[0])
    month = month_from_text(split_text[1])
    return ScheduleDate(schedule, day, month)

def from_schedule_date_range(dates_text: str, parser_format: str) -> pd.DatetimeIndex:
    try:
        from_time, to_time = [datetime.strptime(date_text.strip(), parser_format)
            for date_text in multi_split(clean(dates_text), ['-', ' TO '])
        ]
        return pd.date_range(
            start = from_time,
            end = to_time,
            tz = timezone.get_current_timezone(),
        )
    except ValueError as e:
        print(e)
        print('Using fallback dates')
        return fallback_dates

def get_url(name: str) -> str | list[str]:
    prefix = settings.SCRAPER['URL_PREFIX']
    path = settings.SCRAPER['URL_PATHS'][name]
    if isinstance(path, list):
        return [prefix + one_path for one_path in path]
    return prefix + path

def request_soup(url: str) -> bs:
    sleep(settings.SCRAPER['PAUSE_SECS'])
    req = requests.get(url)
    req.encoding = req.apparent_encoding
    print(f"\nGot {req.status_code} on {req.url}\n")
    return bs(req.text, settings.SCRAPER['PARSER'])
