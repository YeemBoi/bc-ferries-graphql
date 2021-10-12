from django.db import models as m
from common.scraper_utils import get_url

CURRENT_SAILING_STATUS_CHOICES = [
    ('GOOD', 'On time'),
    ('MEDI', 'Medical emergency'),
    ('PEAK', 'Peak travel; Loading max number of vehicles'),
    ('VHCL', 'Loading as many vehicles as possible'),
    ('ONGN', 'Earlier loading procedure causing ongoing delay'),
    ('DELA', 'Vessel start up delay, departing ASAP'),
    ('SHIP', 'Loading and unloading multiple ships'),
    ('CREW', 'Crew member enroute to assist with boarding'),
    ('CNCL', 'Cancelled'),
    ('HELP', 'Helping customers'),
]

class ScrapedModel(m.Model):
    official_page = m.URLField()
    fetched_time = m.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

def Code(length: int = 3) -> m.CharField:
    return m.CharField(max_length=length, unique=True)


class City(m.Model):
    code = Code()
    name = m.CharField(max_length=250)
    sort_order = m.PositiveIntegerField(null=True) # required for "Southern Gulf Islands" cc

    def __str__(self) -> str:
        return self.name

class GeoArea(m.Model):
    code = Code(2)
    name = m.CharField(max_length=250)
    sort_order = m.PositiveIntegerField(null=True)

    def __str__(self) -> str:
        return self.name

class Terminal(ScrapedModel):
    city = m.ForeignKey(City, on_delete=m.CASCADE)
    geo_area = m.ForeignKey(GeoArea, on_delete=m.CASCADE)
    code = Code()
    name = m.CharField(max_length=250)
    travel_route_name = m.CharField(max_length=250)

    def save(self, *args, **kwargs):
        if not self.official_page:
            self.official_page = get_url('TERMINAL').format(self.travel_route_name, self.code)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

class Route(m.Model):
    origin = m.ForeignKey(Terminal, on_delete=m.CASCADE, related_name='destination_routes')
    destination = m.ForeignKey(Terminal, on_delete=m.CASCADE, related_name='origin_routes')

    def scraper_url_param(self) -> str:
        return '-'.join([self.origin.code, self.destination.code])
    
    def scrape(self):
        from .tasks import scrape_route_schedule_task
        return scrape_route_schedule_task.delay(self.pk)

    def __str__(self) -> str:
        return f"{self.origin} to {self.destination}"


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

    def scrape_current_conditions(self):
        from .tasks import scrape_route_schedule_task
        return scrape_route_schedule_task.delay(self.pk)


    def __str__(self) -> str:
        return f"info #{self.original_index}: {self.route}"


class Service(m.Model):
    name = m.CharField(max_length=250)
    is_additional = m.BooleanField()

    def __str__(self) -> str:
        return self.name

class Ferry(ScrapedModel):
    code = Code(4)
    name = m.CharField(max_length=250)
    services = m.ManyToManyField(Service, related_name='providing_ferries')

    built = m.DateField(null=True)
    car_capacity = m.PositiveIntegerField()
    human_capacity = m.PositiveIntegerField()
    horsepower = m.PositiveIntegerField()
    max_displacement = m.FloatField('Max displacement (t)')
    max_speed = m.FloatField('Max speed (knots)')
    total_length = m.FloatField('Total length (m)')

    def __str__(self) -> str:
        return self.name


class Sailing(ScrapedModel):
    route = m.ForeignKey(Route, on_delete=m.CASCADE, related_name='sailings')
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


class CurrentSailing(ScrapedModel):
    route_info = m.ForeignKey(RouteInfo, on_delete=m.CASCADE, related_name='current_sailings')
    ferry = m.ForeignKey(Ferry, null=True, on_delete=m.SET_NULL)
    scheduled_time = m.DateTimeField(null=True)
    actual_time = m.DateTimeField(null=True)
    arrival_time = m.DateTimeField(null=True)
    has_arrived = m.BooleanField()
    standard_vehicle_percentage = m.PositiveIntegerField(default=0)
    mixed_vehicle_percentage = m.PositiveIntegerField(default=0)
    total_capacity_percentage = m.PositiveIntegerField(default=0)
    status = m.CharField(max_length=4, null=True, choices=CURRENT_SAILING_STATUS_CHOICES)

    def save(self, *args, **kwargs):
        if not self.official_page:
            self.official_page = get_url('ROUTE_CONDITIONS').format(self.route_info.route.scraper_url_param())
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.route_info.route}"
