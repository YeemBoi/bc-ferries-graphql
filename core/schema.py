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
            'name': ['exact', 'icontains', 'istartswith'],
            'sort_order': ['exact']
        }
        interfaces = (g.relay.Node, )


class GeoAreaNode(gd.DjangoObjectType):
    class Meta:
        model = m.GeoArea
        filter_fields = {
            'code': ['exact'],
            'name': ['exact', 'icontains', 'istartswith'],
            'sort_order': ['exact']
        }
        interfaces = (g.relay.Node, )


class LocationNode(gd.DjangoObjectType):
    class Meta:
        model = m.Location
        filter_fields = {
            'code': ['exact'],
            'name': ['exact', 'icontains', 'istartswith'],
            'travel_route_name': ['exact'],
            'city': [],
            'geo_area': [],
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
            'name': ['exact', 'icontains', 'istartswith'],
            'is_additional': ['exact'],
        }
        interfaces = (g.relay.Node, )


class ShipNode(gd.DjangoObjectType):
    class Meta:
        model = m.Ship
        filter_fields = {
            'services': [],
            'code': ['exact'],
            'name': ['exact', 'icontains', 'istartswith'],
            'built': ['exact'],
            'car_capacity': ['exact'],
            'human_capacity': ['exact'],
            'horsepower': ['exact'],
            'max_displacement': ['exact'],
            'max_speed': ['exact'],
            'total_length': ['exact'],
            **fkFilters(ServiceNode, 'services'),
        }
        interfaces = (g.relay.Node, )


class SailingNode(gd.DjangoObjectType):
    duration = g.String()
    class Meta:
        model = m.Sailing
        filter_fields = {
            'route': [],
            'duration': ['exact'],
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
            'order': ['exact'],
            **fkFilters(SailingNode, 'sailing'),
            **fkFilters(LocationNode, 'location'),
        }
        interfaces = (g.relay.Node, )


class ScheduledSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.ScheduledSailing
        filter_fields = {
            'sailing': [],
            'time': ['exact'],
            **fkFilters(SailingNode, 'sailing'),
        }
        interfaces = (g.relay.Node, )


class CurrentSailingNode(gd.DjangoObjectType):
    class Meta:
        model = m.CurrentSailing
        filter_fields = {
            'sailing': [],
            'actual_time': ['exact'],
            'arrival_time': ['exact'],
            'capacity': ['exact'],
            'delayed': ['exact'],
            'status': ['exact'],
            **fkFilters(SailingNode, 'sailing'),
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
