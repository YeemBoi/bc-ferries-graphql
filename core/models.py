from django.db import models as m

CURRENT_SAILING_STATUS_CHOICES = [
    ('GOOD', 'On time'),
    ('MEDI', 'Medical emergency'),
    ('PEAK', 'Peak travel; Loading max number of vehicles'),
    ('VHCL', 'Loading as many vehicles as possible'),
    ('ONGN', 'Earlier loading procedure causing ongoing delay'),
    ('SHIP', 'Loading and unloading multiple ships'),
    ('CREW', 'Crew member enroute to assist with boarding'),
    ('CNCL', 'Cancelled'),
    ('HELP', 'Helping customers'),
]

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


class Terminal(m.Model):
    code = Code()
    name = m.CharField(max_length=250)
    travel_route_name = m.CharField(max_length=250)

    city = m.ForeignKey(City, on_delete=m.CASCADE)
    geo_area = m.ForeignKey(GeoArea, on_delete=m.CASCADE)

    def __str__(self) -> str:
        return self.name


class Route(m.Model):
    origin = m.ForeignKey(Terminal, on_delete=m.CASCADE, related_name='destination_routes')
    destination = m.ForeignKey(Terminal, on_delete=m.CASCADE, related_name='origin_routes')

    def __str__(self) -> str:
        return f"from {self.origin} to {self.destination}"


class RouteInfo(m.Model):
    route = m.ForeignKey(Route, on_delete=m.CASCADE, related_name='info_set')
    original_index = m.PositiveIntegerField()
    conditions_are_tracked = m.BooleanField(default=False)

    length_type = m.CharField(max_length=50)

    limited_availability = m.BooleanField()

    is_bookable = m.BooleanField()
    is_walk_on = m.BooleanField()

    allow_motorcycles = m.BooleanField()
    allow_livestock = m.BooleanField()
    allow_walk_on_options = m.BooleanField()
    allow_additional_passenger_types = m.BooleanField()

    def __str__(self) -> str:
        return f"{self.route}"


class Service(m.Model):
    name = m.CharField(max_length=250)
    is_additional = m.BooleanField()

    def __str__(self) -> str:
        return f"{self.name}"


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
        return f"{self.name}"


class Sailing(m.Model):
    route = m.ForeignKey(Route, on_delete=m.CASCADE)
    duration = m.DurationField()

    #stops = m.ManyToManyField(Terminal)
    #transfer = m.ForeignKey('self", null=True, on_delete=m.SET_NULL)

    def __str__(self) -> str:
        return f"{self.route}"


class EnRouteStop(m.Model):
    sailing = m.ForeignKey(Sailing, on_delete=m.CASCADE, related_name='stops')
    terminal = m.ForeignKey(Terminal, on_delete=m.CASCADE)
    is_certain = m.BooleanField()
    is_transfer = m.BooleanField()
    order = m.IntegerField()

    def __str__(self) -> str:
        return f"{'transfer' if self.is_transfer else 'stop'} at {self.terminal} on {self.sailing}"


class ScheduledSailing(m.Model):
    sailing = m.ForeignKey(Sailing, on_delete=m.CASCADE, related_name='scheduled')
    time = m.DateTimeField()

    def __str__(self) -> str:
        return f"{self.sailing} at {self.time.strftime('%c')}"


class CurrentSailing(m.Model):
    sailing = m.ForeignKey(Sailing, on_delete=m.CASCADE, related_name='current')
    ship = m.ForeignKey(Ship, on_delete=m.CASCADE)
    actual_time = m.DateTimeField()
    arrival_time = m.DateTimeField()
    capacity =  m.PositiveIntegerField()
    is_delayed = m.BooleanField()
    status = m.CharField(max_length=4, choices=CURRENT_SAILING_STATUS_CHOICES)

    def __str__(self) -> str:
        return f"{self.sailing}"
