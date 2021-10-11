from . import models as m
from datetime import date, datetime
from common import graphene_utils as u
import graphene as g
import graphene_django as gd


class CityNode(gd.DjangoObjectType):
    class Meta:
        model = m.City
        filter_fields = {
            'code': ['exact'],
            'name': u.lookups(str),
            'sort_order': u.lookups(int),
        }
        interfaces = (g.relay.Node, )

class GeoAreaNode(gd.DjangoObjectType):
    class Meta:
        model = m.GeoArea
        filter_fields = {
            'code': ['exact'],
            'name': u.lookups(str),
            'sort_order': u.lookups(int),
        }
        interfaces = (g.relay.Node, )

class TerminalNode(gd.DjangoObjectType):
    class Meta:
        model = m.Terminal
        filter_fields = {
            'code': ['exact', 'iexact'],
            'name': u.lookups(str),
            'travel_route_name': u.lookups(str),
            'official_page': [],
            **u.fk_filters(CityNode, 'city'),
            **u.fk_filters(GeoAreaNode, 'geo_area'),
        }
        interfaces = (g.relay.Node, )

class RouteNode(gd.DjangoObjectType):
    class Meta:
        model = m.Route
        filter_fields = {
            **u.fk_filters(TerminalNode, 'origin'),
            **u.fk_filters(TerminalNode, 'destination'),
        }
        interfaces = (g.relay.Node, )

class RouteInfoNode(gd.DjangoObjectType):
    class Meta:
        model = m.RouteInfo
        filter_fields = {
            'conditions_are_tracked': ['exact'],
            'original_index': u.lookups(int),
            'length_type': ['exact'],
            'limited_availability': u.lookups(bool),
            'is_bookable': u.lookups(bool),
            'is_walk_on': u.lookups(bool),
            'allow_motorcycles': u.lookups(bool),
            'allow_livestock': u.lookups(bool),
            'allow_walk_on_options': u.lookups(bool),
            'allow_additional_passenger_types': u.lookups(bool),
            **u.fk_filters(RouteNode, 'route'),
        }
        interfaces = (g.relay.Node, )

class ServiceNode(gd.DjangoObjectType):
    class Meta:
        model = m.Service
        filter_fields = {
            'name': u.lookups(str),
            'is_additional': u.lookups(bool),
        }
        interfaces = (g.relay.Node, )

class FerryNode(gd.DjangoObjectType):
    class Meta:
        model = m.Ferry
        filter_fields = {
            'code': ['exact', 'iexact'],
            'name': u.lookups(str),
            'built': u.lookups(date),
            'car_capacity': u.lookups(int),
            'human_capacity': u.lookups(int),
            'horsepower': u.lookups(int),
            'max_displacement': u.lookups(int),
            'max_speed': u.lookups(int),
            'total_length': u.lookups(int),
            'official_page': [],
            **u.fk_filters(ServiceNode, 'services'),
        }
        interfaces = (g.relay.Node, )

class SailingNode(gd.DjangoObjectType):
    duration = g.String()
    class Meta:
        model = m.Sailing
        filter_fields = {
            'duration': u.lookups(int),
            **u.fk_filters(RouteNode, 'route'),
        }
        interfaces = (g.relay.Node, )

class EnRouteStopNode(gd.DjangoObjectType):
    class Meta:
        model = m.EnRouteStop
        filter_fields = {
            'is_transfer': u.lookups(bool),
            'order': u.lookups(int),
            **u.fk_filters(SailingNode, 'sailing'),
            **u.fk_filters(TerminalNode, 'terminal'),
        }
        interfaces = (g.relay.Node, )

class ScheduledSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.ScheduledSailing
        filter_fields = {
            'time': u.lookups(datetime),
            **u.fk_filters(SailingNode, 'sailing'),
        }
        interfaces = (g.relay.Node, )

class CurrentSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.CurrentSailing
        filter_fields = {
            'scheduled_time': u.lookups(datetime),
            'actual_time': u.lookups(datetime),
            'arrival_time': u.lookups(datetime),
            'has_arrived': u.lookups(bool),
            'standard_vehicle_percentage': u.lookups(int),
            'mixed_vehicle_percentage': u.lookups(int),
            'total_capacity_percentage': u.lookups(int),
            'status': ['exact', 'iexact'],
            'official_page': [],
            **u.fk_filters(RouteInfoNode, 'route_info'),
            **u.fk_filters(FerryNode, 'ferry'),
        }
        interfaces = (g.relay.Node, )


class Query(g.ObjectType):
    city,               all_cities              = u.make_filter_relay(CityNode)
    geo_area,           all_geo_areas           = u.make_filter_relay(GeoAreaNode)
    terminal,           all_terminals           = u.make_filter_relay(TerminalNode)
    route,              all_routes              = u.make_filter_relay(RouteNode)
    route_info,         all_route_info          = u.make_filter_relay(RouteInfoNode)
    services,           all_services            = u.make_filter_relay(ServiceNode)
    ferry,              all_ferries             = u.make_filter_relay(FerryNode)
    sailing,            all_sailings            = u.make_filter_relay(SailingNode)
    en_route_stop,      all_en_route_stops      = u.make_filter_relay(EnRouteStopNode)
    scheduled_sailing,  all_scheduled_sailings  = u.make_filter_relay(ScheduledSailingNode)
    current_sailing,    all_current_sailings    = u.make_filter_relay(CurrentSailingNode)
