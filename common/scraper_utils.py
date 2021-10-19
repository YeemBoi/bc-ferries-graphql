import logging
from django.conf import settings
from munch import Munch
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import month_abbr, day_abbr
from dataclasses import dataclass

import re
import requests
from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from time import sleep

SCRAPER_SETTINGS = Munch(settings.SCRAPER)

tz = timezone.get_current_timezone() if settings.USE_TZ else None

class Logger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLevel(SCRAPER_SETTINGS.LOG_LEVEL)

    def soft_print(self, pre: str, val, level: int = logging.DEBUG):
        if val: self.log(level, f"{pre} {val}")
    
    def soft_print_iter(self, pre: str, vals, level: int = logging.DEBUG):
        if len(vals): self.log(level, f"{pre} {', '.join(map(str, vals))}")
    
    def lazy_print_times(self, pre: str, times: dict[str], level: int = logging.DEBUG):
        self.log(level, '%s:\n%s', pre, '\n'.join([
            f"{name}: {time.strftime('%X') if isinstance(time, datetime) else time}"
            for name, time in times.items()
        ]))
    
    def request_soup(self, url: str) -> bs:
        sleep(SCRAPER_SETTINGS.PAUSE_SECS)
        req = requests.get(url)
        if req.status_code == 200:
            level = logging.INFO
        elif req.status_code >= 400:
            level = logging.ERROR
        else:
            level = logging.WARNING
        self.log(level, f"\nGot {req.status_code} on {req.url}\n")
        return bs(req.text, SCRAPER_SETTINGS.PARSER)

logging.setLoggerClass(Logger)
logging.basicConfig()

def clean(text: str) -> str:
    return text.strip().upper()

def clean_tag_text(tag: Tag, preserve_newlines = False, **kwargs) -> str:
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

def date_time_combine(date_val, time_val) -> datetime:
    is_next_day = (time_val.hour == 24)
    combined = datetime(
        year = date_val.year,
        month = date_val.month,
        day = date_val.day,
        hour = 0 if is_next_day else time_val.hour,
        minute = time_val.minute,
        tzinfo = tz,
    )
    if is_next_day:
        combined += timedelta(days=1)
    return combined

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

"""
def pretty_date_range(date_range: pd.DatetimeIndex) -> str:
    return f"{date_range[0].strftime('%x')} - {date_range[-1].strftime('%x')}"
"""

@dataclass
class ScrapedSchedule:
    find_text: str
    def __str__(self) -> str:
        return self.find_text
   
@dataclass
class ScheduleTime(ScrapedSchedule):
    hour: int
    minute: int

def schedule_includes(search_schedule, search_date) -> bool:
    for scheduled_date in search_schedule:
        if scheduled_date.day == search_date.day and scheduled_date.month == search_date.month:
            return True
    return False

def from_schedule_time(schedule: str) -> ScheduleTime:
    schedule = schedule_clean(schedule)
    split_text = schedule.split()
    hour, minute = split_text[0].split(':')
    hour = int(hour)
    if minute.endswith('M'): # eg "6:00PM"
        split_text.append(minute[-2:])
        minute = minute[:-2]
    minute = int(minute)
    if (split_text[1] == 'PM' and hour != 12) or (hour == 12 and split_text[1] == 'AM'):
        hour += 12
    return ScheduleTime(schedule, hour, minute)



def get_url(name: str) -> str | list[str]:
    path = SCRAPER_SETTINGS.URL_PATHS[name]
    if isinstance(path, list):
        return [SCRAPER_SETTINGS.URL_PREFIX + one_path for one_path in path]
    return SCRAPER_SETTINGS.URL_PREFIX + path
