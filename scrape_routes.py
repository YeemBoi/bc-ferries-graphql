#!/usr/bin/python3

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ferries.settings')

import django
django.setup()
import core.models as m

import urllib3 # ha no requests
http = urllib3.PoolManager()
import ujson

ROUTE_INFO_URL = 'http://www.bcferries.com/route-info'


def specificArea(objs, o):
    area, created = objs.get_or_create(
        code = o['code'],
        name = o['name'],
        sort_order = o['sortOrder']
    )
    if created:
        print('created area', area)
    return area


def location(l) -> m.Location:
    loc, created =  m.Location.objects.get_or_create(
        code = l['code'],
        name = l['name'],
        travel_route_name = l['travelRouteName'],
        geo_area = specificArea(m.GeoArea.objects, l['geoGraphicalArea']),
        city = specificArea(m.City.objects, l['city']),
    )
    if created:
        print('created location', loc)
    return loc


def main():
    routes = ujson.loads(http.request('GET', ROUTE_INFO_URL).data.decode('utf-8'))
    for r in routes:
        origin = location(r)
        for rDest in r['destinationRoutes']:
            route, created = m.Route.objects.get_or_create(
                origin = origin,
                dest = location(rDest),
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
                print('created route', route)

if __name__ == '__main__':
    main()

