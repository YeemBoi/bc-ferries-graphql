from core import models as m
from common.scraper_utils import get_url, SCRAPER_SETTINGS

import urllib3
import ujson
from time import sleep
http = urllib3.PoolManager()

def make_geo_area(objs, o: dict[str]):
    area, created = objs.get_or_create(
        code = o['code'],
        name = o['name'],
        sort_order = o['sortOrder']
    )
    if created: print('Created area', area)
    return area


def make_terminal(t: dict[str, str]) -> m.Terminal:
    terminal, created =  m.Terminal.objects.get_or_create(
        code = t['code'],
        name = t['name'],
        travel_route_name = t['travelRouteName'],
        geo_area = make_geo_area(m.GeoArea.objects, t['geoGraphicalArea']),
        city = make_geo_area(m.City.objects, t['city']),
    )
    if created: print('Created terminal', terminal)
    return terminal

def terminals_including(search: list[dict[str]], terminal: m.Terminal) -> list[dict[str]]:
    return list(filter(lambda t: t['code'] == terminal.code, search))


def quick_json(url: str):
    sleep(SCRAPER_SETTINGS.PAUSE_SECS)
    return ujson.loads(http.request('GET', get_url(url)).data.decode('utf-8'))

def run():
    routes = quick_json('ROUTES')
    cc_routes = quick_json('CC_ROUTES')
    
    m.Route.objects.all().delete()
    bulk_route_info = []
    for r in routes:
        origin = make_terminal(r)
        cc_route_main = terminals_including(cc_routes, origin)
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
                    terminals_including(cc_route_main[0]['destinationRoutes'], route.destination)),
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
