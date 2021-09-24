from django.conf import settings
from core import models as m

import urllib3 # ha no requests
import ujson

http = urllib3.PoolManager()

def make_geo_area(objs, o):
    area, created = objs.get_or_create(
        code = o['code'],
        name = o['name'],
        sort_order = o['sortOrder']
    )
    if created:
        print('Created area', area)
    return area


def make_location(l) -> m.Location:
    loc, created =  m.Location.objects.get_or_create(
        code = l['code'],
        name = l['name'],
        travel_route_name = l['travelRouteName'],
        geo_area = make_geo_area(m.GeoArea.objects, l['geoGraphicalArea']),
        city = make_geo_area(m.City.objects, l['city']),
    )
    if created:
        print('Created location', loc)
    return loc


def run():
    routes = ujson.loads(http.request('GET', settings.SCRAPER_ROUTES_URL).data.decode('utf-8'))
    for r in routes:
        origin = make_location(r)
        for rDest in r['destinationRoutes']:
            route, created = m.Route.objects.get_or_create(
                origin = origin,
                dest = make_location(rDest),
                length_type = rDest['routeType'],
                limited_availability = rDest['limitedAvailability'],
                is_bookable = rDest['isBookable'],
                is_walk_on = rDest['isWalkOn'],
                allow_motorcycles = rDest['motorcycleAllowed'],
                allow_livestock = rDest['allowLivestock'],
                allow_walk_on_options = rDest['allowsWalkOnOptions'],
                allow_additional_passenger_types = rDest['allowAdditionalPassengerTypes'],
            )
            if created:
                print('Created route', route)
