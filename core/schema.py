from django.conf import settings

import core.models as m

import graphene as g
import graphene_django as gd
import graphene_django.filter as gdf


def fkFilters(relClass, relName: str) -> dict:
    newFields = dict()
    for field, filters in relClass._meta.filter_fields.items():
        if len(filters):
            newFields[f'{relName}__{field}'] = filters
    return newFields


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


class LocationNode(gd.DjangoObjectType):
    class Meta:
        model = m.Location
        filter_fields = {
            'city': [],
            'geo_area': [],
            'code': ['exact'],
            'name': settings.DEFAULT_STRING_LOOKUPS,
            'travel_route_name': settings.DEFAULT_STRING_LOOKUPS,
            **fkFilters(CityNode, 'city'),
            **fkFilters(GeoAreaNode, 'geo_area'),
        }
        interfaces = (g.relay.Node, )


class RouteNode(gd.DjangoObjectType):
    class Meta:
        model = m.Route
        filter_fields = {
            'origin': [],
            'dest': [],
            'length_type': ['exact'],
            'limited_availability': ['exact'],
            'is_bookable': ['exact'],
            'is_walk_on': ['exact'],
            'allow_motorcycles': ['exact'],
            'allow_livestock': ['exact'],
            'allow_walk_on_options': ['exact'],
            'allow_additional_passenger_types': ['exact'],
            **fkFilters(LocationNode, 'origin'),
            **fkFilters(LocationNode, 'dest'),
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


class ShipNode(gd.DjangoObjectType):
    class Meta:
        model = m.Ship
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
            **fkFilters(ServiceNode, 'services'),
        }
        interfaces = (g.relay.Node, )


class SailingNode(gd.DjangoObjectType):
    duration = g.String()
    class Meta:
        model = m.Sailing
        filter_fields = {
            'route': [],
            'duration': settings.DEFAULT_RANGE_LOOKUPS,
            **fkFilters(RouteNode, 'route'),
        }
        interfaces = (g.relay.Node, )


class EnRouteStopNode(gd.DjangoObjectType):
    class Meta:
        model = m.EnRouteStop
        filter_fields = {
            'sailing': [],
            'location': [],
            'is_transfer': ['exact'],
            'order': settings.DEFAULT_RANGE_LOOKUPS,
            **fkFilters(SailingNode, 'sailing'),
            **fkFilters(LocationNode, 'location'),
        }
        interfaces = (g.relay.Node, )


class ScheduledSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.ScheduledSailing
        filter_fields = {
            'sailing': [],
            'time': settings.DEFAULT_DATETIME_LOOKUPS,
            **fkFilters(SailingNode, 'sailing'),
        }
        interfaces = (g.relay.Node, )


class CurrentSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.CurrentSailing
        filter_fields = {
            'sailing': [],
            'ship': [],
            'actual_time': settings.DEFAULT_DATETIME_LOOKUPS,
            'arrival_time': settings.DEFAULT_DATETIME_LOOKUPS,
            'capacity': settings.DEFAULT_RANGE_LOOKUPS,
            'delayed': ['exact'],
            'status': ['exact'],
            **fkFilters(SailingNode, 'sailing'),
            **fkFilters(ShipNode, 'ship'),
        }
        interfaces = (g.relay.Node, )


class Query(g.ObjectType):
    city = g.relay.Node.Field(CityNode)
    all_cities = gdf.DjangoFilterConnectionField(CityNode)

    geo_area = g.relay.Node.Field(GeoAreaNode)
    all_geo_areas = gdf.DjangoFilterConnectionField(GeoAreaNode)

    location = g.relay.Node.Field(LocationNode)
    all_locations = gdf.DjangoFilterConnectionField(LocationNode)

    route = g.relay.Node.Field(RouteNode)
    all_routes = gdf.DjangoFilterConnectionField(RouteNode)

    services = g.relay.Node.Field(ServiceNode)
    all_services = gdf.DjangoFilterConnectionField(ServiceNode)
    
    ship = g.relay.Node.Field(ShipNode)
    all_ships = gdf.DjangoFilterConnectionField(ShipNode)

    sailing = g.relay.Node.Field(SailingNode)
    all_sailings = gdf.DjangoFilterConnectionField(SailingNode)

    en_route_stop = g.relay.Node.Field(EnRouteStopNode)
    all_en_route_stops = gdf.DjangoFilterConnectionField(EnRouteStopNode)

    scheduled_sailing = g.relay.Node.Field(ScheduledSailingNode)
    all_scheduled_sailings = gdf.DjangoFilterConnectionField(ScheduledSailingNode)

    current_sailing = g.relay.Node.Field(CurrentSailingNode)
    all_current_sailings = gdf.DjangoFilterConnectionField(CurrentSailingNode)
