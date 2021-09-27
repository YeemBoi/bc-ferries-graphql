from django.conf import settings
from core import models as m

from time import sleep
import urllib3 # ha no requests
import ujson

def make_geo_area(objs, o: dict[str]):
    area, created = objs.get_or_create(
        code = o['code'],
        name = o['name'],
        sort_order = o['sortOrder']
    )
    if created:
        print('Created area', area)
    return area


def make_terminal(t: dict[str, str]) -> m.Terminal:
    terminal, created =  m.Terminal.objects.get_or_create(
        code = t['code'],
        name = t['name'],
        travel_route_name = t['travelRouteName'],
        geo_area = make_geo_area(m.GeoArea.objects, t['geoGraphicalArea']),
        city = make_geo_area(m.City.objects, t['city']),
    )
    if created:
        print('Created terminal', terminal)
    return terminal

def includes_terminal(search: list[dict[str]], terminal: m.Terminal) -> list[dict[str]]:
    return [t for t in search if t['code'] == terminal.code]

def run():
    http = urllib3.PoolManager()
    routes = ujson.loads(http.request('GET', settings.SCRAPER_ROUTES_URL).data.decode('utf-8'))
    sleep(settings.SCRAPER_PAUSE_SECS)
    cc_routes = ujson.loads(http.request('GET', settings.SCRAPER_CC_ROUTES_URL).data.decode('utf-8'))
    
    m.Route.objects.all().delete()
    bulk_route_info = []
    for r in routes:
        origin = make_terminal(r)
        cc_route_main = includes_terminal(cc_routes, origin)
        for i, r_dest in enumerate(r['destinationRoutes']):
            route, created = m.Route.objects.get_or_create(
                origin = origin,
                destination = make_terminal(r_dest),
            )
            if created:
                print('Created route', route)
            
            bulk_route_info.append(m.RouteInfo(
                route = route,
                original_index = i,
                conditions_are_tracked = bool(cc_route_main and
                    includes_terminal(cc_route_main[0]['destinationRoutes'], route.destination)),
                length_type = r_dest['routeType'],
                limited_availability = r_dest['limitedAvailability'],
                is_bookable = r_dest['isBookable'],
                is_walk_on = r_dest['isWalkOn'],
                allow_motorcycles = r_dest['motorcycleAllowed'],
                allow_livestock = r_dest['allowLivestock'],
                allow_walk_on_options = r_dest['allowsWalkOnOptions'],
                allow_additional_passenger_types = r_dest['allowAdditionalPassengerTypes'],
            ))
    m.RouteInfo.objects.bulk_create(bulk_route_info)
