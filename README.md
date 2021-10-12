# BC Ferries GraphQL API
Unofficial but comprehensive BC Ferries GraphQL API &amp; scraper, built with Django.


Includes highly detailed data on locations, terminals, routes, schedules, conditions, ferries, and services.

## GraphQL Schema
GraphQL schema is available at [`schema.graphql`](schema.graphql). A JSON schema is also available.

- Thanks to Graphene, a GraphiQL endpoint is available at `/graphql`
- JWT auth (optional) with [`django-graphql-jwt`](https://django-graphql-jwt.domake.io/)
- Extensive filtering options, including relations

Check out some example queries at [`examples.graphql`](examples.graphql)!

## Scraping data

Scraping scripts are integrated with [`django-extensions`](https://django-extensions.readthedocs.io/),
and should be run through `./manage.py runscript foo`

### Scrape everything
To initialize the database with all data, run `./manage.py runscript init_scraped_data`

### Scrape specific elements
- Routes, terminals, cities, regions: `./manage.py runscript scrape_routes`
- Ferries, services, amenities: `./manage.py runscript scrape_fleet`
- Sailings, scheduled sailings, en-route stops & transfers: `./manage.py runscript scrape_schedule`
- Current sailings / conditions: `./manage.py runscript scrape_current_conditions`

### Performance
Scraping should not be resource intensive, but by default there is a 10-second delay between http requests to BC Ferries to abide by [`robots.txt`](http://bcferries.com/robots.txt).
This can be changed in `settings.SCRAPER_PAUSE_SECS`.

### Scheduling
Scraping operations can also be run as asynchronous tasks via Celery (Redis as a broker and result backend). By default these are scheduled in Celery Beat, running no more than weekly with the exception of current conditions scraping, which runs every 5 minutes. Keep in mind that these tasks will be most effective after initializing other data, e.g. routes and ferries.

## [Default settings](ferries/settings.py)
```python
SCRAPER = {
    'PARSER':               'html5lib',         # used by bs4
    'PAUSE_SECS':           0 if DEBUG else 10, # See http://bcferries.com/robots.txt
    'FALLBACK_DAY_PERIODS': 100,                # How many days into the future to attempt to create schedules for
    'FLEET_PAGE_RANGE':     2,
    'LOG_LEVEL':            logging.DEBUG,
    'INIT_SCRIPTS': [       # Used by init_scraped_data script
        'save_sitemap',
        'scrape_routes',
        'scrape_fleet',
        'scrape_schedule',
        'scrape_current_conditions',
    ],
    'URL_PREFIX': 'https://www.bcferries.com',
    'URL_PATHS': {
        'SCHEDULES':            '/routes-fares/schedules',
        'CONDITIONS':           '/current-conditions',
        'DEPARTURES':           '/current-conditions/departures',
        'ROUTE_CONDITIONS':     '/current-conditions/{}',
        'ROUTES':               '/route-info',
        'CC_ROUTES':            '/cc-route-info',
        'FLEET':                '/on-the-ferry/our-fleet?page={}',
        'SCHEDULE_SEASONAL':    '/routes-fares/schedules/seasonal/{}',
        'SCHEDULE_DATES':       '/getDepartureDates?origin={}&destination={}&selectedMonth={}&selectedYear={}',
        'DEPARTURES':           '/current-conditions/departures',
        'TERMINAL':             '/travel-boarding/terminal-directions-parking-food/{}/{}',
        'SHIP':                 '/on-the-ferry/our-fleet/{}/{}',
        'SCHEDULES':            '/routes-fares/schedules',
        'MISC_SCHEDULES': [
            '/routes-fares/schedules/southern-gulf-islands',
          # '/routes-fares/schedules/gambier-keats',
        ],
    },
}

_RANGE_LOOKUPS  = ['exact', 'gt', 'lt', 'gte', 'lte']
_use_range_lookups = lambda dt: [f'{dt}__{lookup}' for lookup in _RANGE_LOOKUPS]
_use_unnested_range_lookups = lambda lt: itertools.chain(*[_use_range_lookups(lookupType) for lookupType in lt])
_DATE_LOOKUPS = ['year', 'month', 'day', 'week_day']
_TIME_LOOKUPS = ['hour', 'minute']

from datetime import date, time, datetime, timedelta
DEFAULT_LOOKUPS = {
    str: ['exact', 'iexact', 'regex', 'icontains'],
    bool: ['exact'],
    int: _RANGE_LOOKUPS,
    date: [
        *_RANGE_LOOKUPS,
        *_use_unnested_range_lookups(_DATE_LOOKUPS),
    ],
    time: [
        *_RANGE_LOOKUPS,
        *_use_unnested_range_lookups(_TIME_LOOKUPS),
    ],
    datetime: [
        *_RANGE_LOOKUPS,
        *_use_range_lookups('date'),
        *_use_unnested_range_lookups(_DATE_LOOKUPS),
        *_use_range_lookups('time'),
        *_use_unnested_range_lookups(_TIME_LOOKUPS),
    ],
    timedelta: _RANGE_LOOKUPS,
}
```
