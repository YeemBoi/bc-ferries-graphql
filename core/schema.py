from django.conf import settings
from . import models as m
from common import graphene_utils as gu
import graphene as g
import graphene_django as gd


class CityNode(gd.DjangoObjectType):
    class Meta:
        model = m.City
        filter_fields = {
            'code': ['exact'],
            'name': settings.DEFAULT_STRING_LOOKUPS,
            'sort_order': settings.DEFAULT_RANGE_LOOKUPS,
        }
        interfaces = (g.relay.Node, )

class GeoAreaNode(gd.DjangoObjectType):
    class Meta:
        model = m.GeoArea
        filter_fields = {
            'code': ['exact'],
            'name': settings.DEFAULT_STRING_LOOKUPS,
            'sort_order': settings.DEFAULT_RANGE_LOOKUPS,
        }
        interfaces = (g.relay.Node, )

class TerminalNode(gd.DjangoObjectType):
    class Meta:
        model = m.Terminal
        filter_fields = {
            'city': [],
            'geo_area': [],
            'code': ['exact'],
            'name': settings.DEFAULT_STRING_LOOKUPS,
            'travel_route_name': settings.DEFAULT_STRING_LOOKUPS,
            'official_page': [],
            **gu.fk_filters(CityNode, 'city'),
            **gu.fk_filters(GeoAreaNode, 'geo_area'),
        }
        interfaces = (g.relay.Node, )

class RouteNode(gd.DjangoObjectType):
    class Meta:
        model = m.Route
        filter_fields = {
            'origin': [],
            'destination': [],
            **gu.fk_filters(TerminalNode, 'origin'),
            **gu.fk_filters(TerminalNode, 'destination'),
        }
        interfaces = (g.relay.Node, )

class RouteInfoNode(gd.DjangoObjectType):
    class Meta:
        model = m.RouteInfo
        filter_fields = {
            'route': [],
            'conditions_are_tracked': ['exact'],
            'original_index': settings.DEFAULT_RANGE_LOOKUPS,
            'length_type': ['exact'],
            'limited_availability': ['exact'],
            'is_bookable': ['exact'],
            'is_walk_on': ['exact'],
            'allow_motorcycles': ['exact'],
            'allow_livestock': ['exact'],
            'allow_walk_on_options': ['exact'],
            'allow_additional_passenger_types': ['exact'],
            **gu.fk_filters(RouteNode, 'route'),
        }
        interfaces = (g.relay.Node, )

class ServiceNode(gd.DjangoObjectType):
    class Meta:
        model = m.Service
        filter_fields = {
            'name': settings.DEFAULT_STRING_LOOKUPS,
            'is_additional': ['exact'],
        }
        interfaces = (g.relay.Node, )

class FerryNode(gd.DjangoObjectType):
    class Meta:
        model = m.Ferry
        filter_fields = {
            'services': [],
            'code': ['exact'],
            'name': settings.DEFAULT_STRING_LOOKUPS,
            'built': settings.DEFAULT_DATE_LOOKUPS,
            'car_capacity': settings.DEFAULT_RANGE_LOOKUPS,
            'human_capacity': settings.DEFAULT_RANGE_LOOKUPS,
            'horsepower': settings.DEFAULT_RANGE_LOOKUPS,
            'max_displacement': settings.DEFAULT_RANGE_LOOKUPS,
            'max_speed': settings.DEFAULT_RANGE_LOOKUPS,
            'total_length': settings.DEFAULT_RANGE_LOOKUPS,
            'official_page': [],
            **gu.fk_filters(ServiceNode, 'services'),
        }
        interfaces = (g.relay.Node, )

class SailingNode(gd.DjangoObjectType):
    duration = g.String()
    class Meta:
        model = m.Sailing
        filter_fields = {
            'route': [],
            'duration': settings.DEFAULT_RANGE_LOOKUPS,
            **gu.fk_filters(RouteNode, 'route'),
        }
        interfaces = (g.relay.Node, )

class EnRouteStopNode(gd.DjangoObjectType):
    class Meta:
        model = m.EnRouteStop
        filter_fields = {
            'sailing': [],
            'terminal': [],
            'is_transfer': ['exact'],
            'order': settings.DEFAULT_RANGE_LOOKUPS,
            **gu.fk_filters(SailingNode, 'sailing'),
            **gu.fk_filters(TerminalNode, 'terminal'),
        }
        interfaces = (g.relay.Node, )

class ScheduledSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.ScheduledSailing
        filter_fields = {
            'sailing': [],
            'time': settings.DEFAULT_DATETIME_LOOKUPS,
            **gu.fk_filters(SailingNode, 'sailing'),
        }
        interfaces = (g.relay.Node, )

class CurrentSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.CurrentSailing
        filter_fields = {
            'route_info': [],
            'ferry': [],
            'actual_time': settings.DEFAULT_DATETIME_LOOKUPS,
            'arrival_time': settings.DEFAULT_DATETIME_LOOKUPS,
            'capacity': settings.DEFAULT_RANGE_LOOKUPS,
            'is_delayed': ['exact'],
            'status': ['exact'],
            **gu.fk_filters(RouteInfoNode, 'route_info'),
            **gu.fk_filters(FerryNode, 'ferry'),
        }
        interfaces = (g.relay.Node, )


class Query(g.ObjectType):
    city,               all_cities              = gu.make_filter_relay(CityNode)
    geo_area,           all_geo_areas           = gu.make_filter_relay(GeoAreaNode)
    terminal,           all_terminals           = gu.make_filter_relay(TerminalNode)
    route,              all_routes              = gu.make_filter_relay(RouteNode)
    route_info,         all_route_info          = gu.make_filter_relay(RouteInfoNode)
    services,           all_services            = gu.make_filter_relay(ServiceNode)
    ferry,              all_ferries             = gu.make_filter_relay(FerryNode)
    sailing,            all_sailings            = gu.make_filter_relay(SailingNode)
    en_route_stop,      all_en_route_stops      = gu.make_filter_relay(EnRouteStopNode)
    scheduled_sailing,  all_scheduled_sailings  = gu.make_filter_relay(ScheduledSailingNode)
    current_sailing,    all_current_sailings    = gu.make_filter_relay(CurrentSailingNode)
