from django.utils import timezone
from ferries import models as m

from datetime import datetime, timedelta
from common import scraper_utils as u

from dataclasses import dataclass
from bs4.element import Tag
import re
import logging
log: u.Logger = logging.getLogger(__name__)

@dataclass
class CurrentScheduleTime(u.ScheduleTime):
    is_tomorrow: bool

    def to_datetime(self) -> datetime:
        base_date = timezone.now().date()
        if self.is_tomorrow:
            base_date += timedelta(days=1)
        return u.date_time_combine(base_date, self)

def from_current_datetime(base_time: str, is_tomorrow: bool) -> datetime:
    schedule_time = u.from_schedule_time(base_time)
    return CurrentScheduleTime(
        find_text = schedule_time.find_text,
        hour = schedule_time.hour,
        minute = schedule_time.minute,
        is_tomorrow = is_tomorrow,
    ).to_datetime()

def get_ferry_from_href(a: Tag) -> m.Ferry:
    code = list(filter(None, a['href'].split('/')))[-1] or a.get_text(strip=True)
    try: return m.Ferry.objects.get(code=code)
    except m.Ferry.DoesNotExist: return None

def scrape_conditions_tables():
    global conditions_tables # used for getting more details on past departures
    conditions_tables = log.request_soup(u.get_url('DEPARTURES')).select('.departures-tbl')

STATUS_TEXTS = {
    'ON TIME': 'GOOD',
    'EARLIER LOADING PROCEDURE IS CAUSING ONGOING DELAY': 'ONGN',
    'CANCELLED': 'CNCL',
    'VESSEL START UP DELAY. DEPARTING AS SOON POSSIBLE.': 'DELA',
    'PEAK TRAVEL. LOADING MAXIMUM NUMBER OF VEHICLES': 'PEAK',
    'WE ARE LOADING AS MANY VEHICLES AS POSSIBLE': 'VHCL',
    'WE ARE LOADING AND UNLOADING MULTIPLE SHIPS': 'SHIP',
    'HELPING CUSTOMERS WHO NEED ASSISTANCE BOARDING': 'HELP',
    'A MECHANICAL ISSUE IS CAUSING ONGOING DELAYS': 'MECH',
}

def get_current_sailings(route_info: m.RouteInfo):
    time_initiated = timezone.now()
    if not route_info.conditions_are_tracked:
        raise ValueError(f"conditions on {route_info} are not tracked")
    route: m.Route = route_info.route
    log.info(f"Getting conditions on {route}")
    # used for getting more details on future departures
    url = u.get_url('ROUTE_CONDITIONS').format(route.scraper_url_param())
    soup = log.request_soup(url)
    main_rows = soup.select_one('.detail-departure-table').find('tbody').select('tr')
    tbl_search_title = f"{route.origin} - {route.destination}".upper()
    conditions_rows = []
    for table in conditions_tables:
        if u.clean_tag_text(table.find('b')) == tbl_search_title:
            conditions_rows = table.select('.padding-departures-td') # actually a tr tag
    log.info(f"Found {len(conditions_rows)} conditions entries on main departures page")
    sailings: list[tuple[dict[str]]] = []
    for row in main_rows:
        if 'toggle-div' in row.get('class', []):
            if not len(sailings): continue
            sailings[-1][1]['ferry'] = get_ferry_from_href(row.select_one('.sailing-ferry-name'))
            CAPACITY_PERCENTAGES = [
                'total_capacity_percentage',
                'standard_vehicle_percentage',
                'mixed_vehicle_percentage',
            ]
            for i, bar in enumerate(row.select('.progress-bar')):
                sailings[-1][1][CAPACITY_PERCENTAGES[i]] = int(bar['aria-valuenow'])
        else:
            cols = list(map(u.clean_tag_text, row.select('td', limit=2)))
            if len(cols) != 2:
                log.debug(f"Skipping row, found {len(cols)} cols")
                continue
            time_text, mid_col_text = cols
            key_time = from_current_datetime(' '.join(time_text.split()[:2]), ('TOMORROW' in time_text))
            scheduled_time = None
            actual_time = None
            arrival_time = None
            if has_arrived := 'ARRIVED: ' in mid_col_text:
                mid_col_text = mid_col_text.replace('ARRIVED: ', '')
            if has_arrived or ('ETA: ' in mid_col_text):
                actual_time = key_time
                arrival_time = from_current_datetime(mid_col_text.replace('ETA: ', ''), False)
            else:
                scheduled_time = key_time
            log.debug(mid_col_text)
            sailings.append(({
                'scheduled_time': scheduled_time,
                'actual_time': actual_time,
                'arrival_time': arrival_time,
                'has_arrived': has_arrived,
            }, dict()))
    for core_times, extra_details in sailings:
        log.lazy_print_times('Core times', core_times)
        m.CurrentSailing.objects.update_or_create(
            route_info = route_info,
            **core_times,
            defaults = {
                'official_page': url,
                **extra_details,
            },
        )
    for row in conditions_rows:
        cols = row.select('td')
        if len(cols) != 3:
            u.debug('Skipping row, found', len(cols), 'cols')
            continue
        times: dict[str, datetime] = dict()
        for time_l in cols[1].select('.departures-time-ul'):
            if not u.clean_tag_text(time_l): continue
            time_name, time_val = list(map(u.clean_tag_text, time_l.select('li')))
            try: times[time_name.replace(':', '')] = from_current_datetime(time_val, False)
            except ValueError as e: log.warning("Could not parse time", exc_info=e)
        
        arrival_time = None
        has_arrived = False
        if 'ARRIVAL' in times:
            arrival_time = times['ARRIVAL']
            has_arrived = True
        elif 'ETA' in times and times['ETA'] != 'VARIABLE':
            arrival_time = times['ETA']
        defaults = {
            'status': STATUS_TEXTS.get(u.clean_tag_text(cols[2])),
            'ferry': get_ferry_from_href(cols[0].find('a'))
        }
        sailing: m.CurrentSailing
        created: bool
        if 'ACTUAL' in times:
            if 'SCHEDULED' in times: defaults['scheduled_time'] = times['SCHEDULED']
            sailing, created = m.CurrentSailing.objects.update_or_create(
                route_info = route_info,
                actual_time = times['ACTUAL'],
                arrival_time = arrival_time,
                scheduled_time = None,
                has_arrived = has_arrived,
                defaults = defaults,
            )
        else:
            sailing, created = m.CurrentSailing.objects.update_or_create(
                route_info = route_info,
                scheduled_time = times['SCHEDULED'],
                arrival_time = None,
                actual_time = None,
                has_arrived = False,
                defaults = {
                    'arrival_time': arrival_time,
                    **defaults,
                }
            )
        if created: log.warning('Created new sailing from departures page')
        log.lazy_print_times('Sailing attributes', {
            name: getattr(sailing, name)
            for name in ['scheduled_time', 'actual_time', 'arrival_time', 'has_arrived',
                'total_capacity_percentage', 'standard_vehicle_percentage', 'mixed_vehicle_percentage',
                'ferry', 'status',
            ]
        })
        # sailing.save()
    m.CurrentSailing.objects.filter(
        route_info = route_info,
        fetched_time__lt = time_initiated - timedelta(minutes=1)
    ).delete()

def run():
    scrape_conditions_tables()
    for tracked_route_info in m.RouteInfo.objects.filter(conditions_are_tracked=True):
        get_current_sailings(tracked_route_info)
