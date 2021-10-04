from django.conf import settings
from django.utils import timezone
from core import models as m

from datetime import datetime, timedelta, tzinfo
from common import scraper_utils as u

from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class CurrentScheduleTime(u.ScheduleTime):
    is_tomorrow: bool

    def to_datetime(self) -> datetime:
        base_date = timezone.now().date()
        if self.is_tomorrow:
            base_date += timedelta(days=1)
        return datetime(
            year = base_date.year,
            month = base_date.month,
            day = base_date.day,
            hour = self.hour,
            minute = self.minute,
            tzinfo = timezone.get_current_timezone()
        )

# used for getting more details on past departures
conditions_soup = u.request_soup(settings.SCRAPER_DEPARTURES_URL)

def get_current_sailings(route_info: m.RouteInfo):
    if not route_info.conditions_are_tracked:
        raise ValueError(f"conditions on {route_info} are not tracked")
    route: m.Route = route_info.route
    # used for getting more details on future departures
    soup = u.request_soup(settings.SCRAPER_ROUTE_CONDITIONS_URL.format(route.scraper_url_param()))
    main_rows = soup.select_one('.detail-departure-table').find('tbody').select('tr')
    timed_departures: dict[CurrentScheduleTime, m.CurrentSailing] = dict()
    last_row: Optional[CurrentScheduleTime] = None
    for i, row in enumerate(main_rows):
        cols = row.select('td')
        if len(cols) != 3:
            print('Skipping row, found', len(cols), 'cols')
            continue

    

def run():
    for tracked_route_info in m.RouteInfo.objects.filter(conditions_are_tracked=True):
        get_current_sailings(tracked_route_info)

