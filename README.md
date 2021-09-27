# BC Ferries GraphQL API
Unofficial but comprehensive BC Ferries GraphQL API &amp; scraper, built with Django.


Includes highly detailed data on locations, routes, schedules, and ships.

## Schema
GraphQL schema is available at [`schema.json`](schema.json)

- Thanks to Graphene, a GraphiQL endpoint is available at `/graphql`
- JWT auth (optional) with `django-graphql-jwt`
- Extensive filtering options, including relations

## Scraping data

Scraping scripts are integrated with `django-extensions`,
and should be run through `manage.py runscript scrape_foo`

### Scrape everything
To initialize the database with all data, run `manage.py runscript init_scraped_data`

### Scrape specific elements
- Routes, locations, cities, regions: `manage.py runscript scrape_routes`
- Ships, services, amenities: `manage.py runscript scrape_fleet`
- Sailings, scheduled sailings, en-route stops & transfers: `manage.py runscript scrape_schedule`

### Performance
Scraping should not be resource intensive, but by default there is a 10-second delay between http requests to BC Ferries to abide by [`robots.txt`](http://bcferries.com/robots.txt).
This can be changed in `settings.SCRAPER_PAUSE_SECS`.

## Example queries

### Terminals:
```graphql
query {
  allTerminals- {
    edges {
      node {
        city {
          code
          name
          sortOrder
          id
        }
        geoArea {
          code
          name
          sortOrder
          id
        }
        code
        name
        travelRouteName
        id
      }
    }
  }
}
```

### Route:
```graphql
query ($originCode: String, $destCode: String) {
  allRoutes(origin_Code: $originCode, destination_Code: $destCode) {
    edges {
      node {
        origin {
          code
          name
          travelRouteName
          id
        }
        destination {
          code
          name
          travelRouteName
          id
        }
        infoSet {
          edges {
            node {
              lengthType
              limitedAvailability
              isBookable
              isWalkOn
              allowMotorcycles
              allowLivestock
              allowWalkOnOptions
              allowAdditionalPassengerTypes
              id
            }
          }
        }
        id
      }
    }
  }
}
```

### Ship:
```graphql
query ($code: String) {
  allShips(code: $code) {
    edges {
      node {
        services {
          edges {
            node {
              name
              isAdditional
              id
            }
          }
        }
        code
        name
        built
        carCapacity
        humanCapacity
        horsepower
        maxDisplacement
        maxSpeed
        totalLength
        id
      }
    }
  }
}
```

### Sailing:
```graphql
query ($originCode: String, $destCode: String $scheduledUntil: DateTime) {
  allSailings(route_Origin_Code: $originCode, route_Destination_Code: $destCode) {
    edges {
      node {
        current {
          edges {
            node {
              actualTime
              arrivalTime
              capacity
              isDelayed
              status
              id
            }
          }
        }
        scheduled(time_Lte: $scheduledUntil) {
          edges {
            node {
              time
              id
            }
          }
        }
        stops {
          edges {
            node {
              location {
                name
                code
                id
              }
              isTransfer
              order
              id
            }
          }
        }
        id
      }
    }
  }
}
```

## [Default settings](ferries/settings.py)
```python
# See http://bcferries.com/robots.txt
SCRAPER_PAUSE_SECS = 10

SCRAPER_URL_PREFIX            = 'http://www.bcferries.com'
SCRAPER_SCHEDULES_URL         = SCRAPER_URL_PREFIX + '/routes-fares/schedules'
SCRAPER_CONDITIONS_URL        = SCRAPER_URL_PREFIX + '/current-conditions'
SCRAPER_DEPARTURES_URL        = SCRAPER_URL_PREFIX + '/current-conditions/departures'
SCRAPER_ROUTES_URL            = SCRAPER_URL_PREFIX + '/route-info'
SCRAPER_CC_ROUTES_URL         = SCRAPER_URL_PREFIX + '/cc-route-info'
SCRAPER_FLEET_URL             = SCRAPER_URL_PREFIX + '/on-the-ferry/our-fleet?page={}'
SCRAPER_SCHEDULE_SEASONAL_URL = SCRAPER_URL_PREFIX + '/routes-fares/schedules/seasonal/{}-{}'
SCRAPER_SCHEDULE_DAILY_URL    = SCRAPER_URL_PREFIX + '/routes-fares/schedules/daily/{}-{}'
SCRAPER_SCHEDULE_URL          = SCRAPER_URL_PREFIX + '/getDepartureDates?origin={}&destination={}&selectedMonth=8&selectedYear={}'
SCRAPER_FLEET_PAGE_RANGE      = 2

SCRAPER_MISC_SCHEDULE_URLS = [
    SCRAPER_URL_PREFIX + '/routes-fares/schedules/southern-gulf-islands',
]

# How many days into the future to attempt to create schedules for
SCRAPER_FALLBACK_DATE_PERIODS = 100

# BC Ferries doesn't use alt tags on all images, so map image src to amenities
SCRAPER_AMENITY_IMAGE_PATHS = {
    '/web_image/h8e/h8d/8800764362782.jpg': 'Arbutus Coffee Bar',
    '/web_image/h81/h88/8798826168350.jpg': 'Aurora Lounge',
    '/web_image/h03/h6d/8798746312734.jpg': 'Canoe Cafe',
    '/web_image/h41/hd5/8798823022622.jpg': 'Coast Cafe Express',
    '/web_image/hcb/hd0/8798832164894.jpg': 'Coastal Cafe',
    '/web_image/h9d/h69/8800604258334.jpg': 'Pacific Buffet',
    '/web_image/haa/hf3/8800605044766.jpg': 'Passages',
    '/web_image/h20/h0b/8798760566814.jpg': 'SeaWest Lounge',
    '/web_image/h44/h77/8798814371870.jpg': 'Sitka Coffee Place',
    '/web_image/hf7/hb3/8798767808542.jpg': 'The Raven Lounge',
    '/web_image/h6a/h96/8798810800158.jpg': 'Vista Restaurant',
}

# Used by init_scraped_data script
SCRAPER_SCRIPTS = [
    'save_sitemap',
    'scrape_routes',
    'scrape_fleet',
    'scrape_schedule',
]

DEFAULT_STRING_LOOKUPS = ['exact', 'iexact', 'regex', 'icontains', 'istartswith']
DEFAULT_RANGE_LOOKUPS  = ['exact', 'gt', 'lt', 'gte', 'lte']

_use_default_range_lookups = lambda dt : [f'{dt}__{lookup}' for lookup in DEFAULT_RANGE_LOOKUPS]
_use_unnested_range_lookups = lambda lt : itertools.chain(*[_use_default_range_lookups(lookupType) for lookupType in lt])

_DEFAULT_DATE_LOOKUP_TYPES = ['year', 'iso_year', 'month', 'day', 'week', 'week_day', 'iso_week_day', 'quarter']
_DEFAULT_TIME_LOOKUP_TYPES = ['hour', 'minute', 'second']

DEFAULT_DATE_LOOKUPS = [
    *DEFAULT_RANGE_LOOKUPS,
    *_use_unnested_range_lookups(_DEFAULT_DATE_LOOKUP_TYPES),
]
DEFAULT_TIME_LOOKUPS = [
    *DEFAULT_RANGE_LOOKUPS,
    *_use_unnested_range_lookups(_DEFAULT_TIME_LOOKUP_TYPES),
]
DEFAULT_DATETIME_LOOKUPS = [
    *DEFAULT_RANGE_LOOKUPS,
    *_use_default_range_lookups('date'),
    *_use_unnested_range_lookups(_DEFAULT_DATE_LOOKUP_TYPES),
    *_use_default_range_lookups('time'),
    *_use_unnested_range_lookups(_DEFAULT_TIME_LOOKUP_TYPES),
]
```
