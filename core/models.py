from django.conf import settings
from django.db import models as m


def Code(length: int = 3) -> m.CharField:
    return m.CharField(max_length=length, unique=True)


class City(m.Model):
    code = Code()
    name = m.CharField(max_length=250)
    sort_order = m.PositiveIntegerField()

    def __str__(self) -> str:
        return self.name


class GeoArea(m.Model):
    code = Code()
    name = m.CharField(max_length=250)
    sort_order = m.PositiveIntegerField()

    def __str__(self) -> str:
        return self.name


class Location(m.Model):
    code = Code()
    name = m.CharField(max_length=250)
    travel_route_name = m.CharField(max_length=250)

    city = m.ForeignKey(City, on_delete=m.CASCADE)
    geo_area = m.ForeignKey(GeoArea, on_delete=m.CASCADE)

    def __str__(self) -> str:
        return self.name


class Route(m.Model):
    origin = m.ForeignKey(Location, on_delete=m.CASCADE, related_name='destination_routes')
    dest = m.ForeignKey(Location, on_delete=m.CASCADE, related_name='origin_routes')
    length_type = m.CharField(max_length=50)

    limited_availability = m.BooleanField()

    is_bookable = m.BooleanField()
    is_walk_on = m.BooleanField()

    allow_motorcycles = m.BooleanField()
    allow_livestock = m.BooleanField()
    allow_walk_on_options = m.BooleanField()
    allow_additional_passenger_types = m.BooleanField()

    def __str__(self) -> str:
        return f'from {self.origin} to {self.dest}'


class Service(m.Model):
    name = m.CharField(max_length=250)
    is_additional = m.BooleanField()

    def __str__(self) -> str:
        return self.name


class Ship(m.Model):
    code = Code(4)
    name = m.CharField(max_length=250)
    services = m.ManyToManyField(Service, related_name='providing_ships')

    built = m.DateField(null=True)
    car_capacity = m.PositiveIntegerField()
    human_capacity = m.PositiveIntegerField()
    horsepower = m.PositiveIntegerField()
    max_displacement = m.FloatField('Max displacement (t)')
    max_speed = m.FloatField('Max speed (knots)')
    total_length = m.FloatField('Total length (m)')

    def __str__(self) -> str:
        return self.name


class Sailing(m.Model):
    route = m.ForeignKey(Route, on_delete=m.CASCADE)
    duration = m.DurationField()

    #stops = m.ManyToManyField(Location)
    #transfer = m.ForeignKey('self', null=True, on_delete=m.SET_NULL)

    def __str__(self) -> str:
        return f'{self.route}'


class EnRouteStop(m.Model):
    sailing = m.ForeignKey(Sailing, on_delete=m.CASCADE, related_name='stops')
    location = m.ForeignKey(Location, on_delete=m.CASCADE)
    is_transfer = m.BooleanField()
    order = m.IntegerField()

    def __str__(self) -> str:
        return '{} at {} on {}'.format('transfer' if self.is_transfer else 'stop', self.location, self.sailing)


class ScheduledSailing(m.Model):
    sailing = m.ForeignKey(Sailing, on_delete=m.CASCADE, related_name='scheduled')
    time = m.DateTimeField()

class CurrentSailing(m.Model):
    sailing = m.ForeignKey(Sailing, on_delete=m.CASCADE, related_name='current')
    ship = m.ForeignKey(Ship, on_delete=m.CASCADE)
    actual_time = m.DateTimeField()
    arrival_time = m.DateTimeField()
    capacity =  m.PositiveIntegerField()
    delayed = m.BooleanField()
    status = m.CharField(max_length=4, choices = settings.CURRENT_SAILING_STATUS_CHOICES)
