from django.conf import settings

from django.utils import timezone
from datetime import date, datetime, timedelta
from calendar import Calendar, month_abbr

import re
import pandas as pd
from dataclasses import dataclass


fallbackDates = pd.date_range(
    start = datetime.today(),
    periods = settings.SCRAPER_FALLBACK_DATE_PERIODS,
    freq = '1D',
    tz = timezone.get_current_timezone(),
)

def multi_split(mainStr: str, delimiters: list) -> list:
    return re.split(
        '|'.join({re.escape(delimiter) for delimiter in delimiters}),
        mainStr
    )

def month_from_text(text: str) -> int:
    cleanedText = text.strip().upper()
    for i, abbr in enumerate(month_abbr):
        if abbr.upper() == cleanedText:
            return i

def pretty_date_range(dateRange: pd.DatetimeIndex) -> str:
    return f'{dateRange[0].strftime("%x")} - {dateRange[-1].strftime("%x")}'

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

def schedule_includes(searchSchedule, searchDate) -> bool:
    for scheduledDate in searchSchedule:
        if scheduledDate.day == searchDate.day and scheduledDate.month == searchDate.month:
            return True
    return False

def from_schedule_time(schedule: str) -> ScheduleTime:
    findText = schedule.replace('*', '').replace(',', '').strip().upper()
    splitText = findText.split()
    hour, minute = splitText[0].split(':')
    hour = int(hour) -1
    minute = int(minute)
    if splitText[1] == 'PM':
        hour += 12
    return ScheduleTime(findText, hour, minute)

def from_schedule_date(schedule: str) -> ScheduleDate:
    findText = schedule.replace('*', '').replace(',', '').strip().upper()
    splitText = findText.split()
    day = int(splitText[0])
    month = month_from_text(splitText[1])
    return ScheduleDate(findText, day, month)

def from_schedule_date_range(datesText: str) -> pd.DatetimeIndex:
    try:
        fromTime, toTime = [datetime.strptime(dateText.strip(), '%b %d, %Y')
            for dateText in multi_split(datesText.upper(), ['-', ' TO '])
        ]
        return pd.date_range(
            start=fromTime,
            end=toTime,
            tz = timezone.get_current_timezone(),
        )
    except ValueError as e:
        print(e)
        return fallbackDates

def date_range_url_param(dateRange: pd.DatetimeIndex) -> str:
        return '-'.join([dateVal.strftime('%Y%m%d')
            for dateVal in [dateRange[0], dateRange[-1]]])

def run():
    raise ImportError('Utils is not a script')