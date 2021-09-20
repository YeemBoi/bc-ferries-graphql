from django.contrib import admin as a
from . import models as m

a.site.register([
    m.City,
    m.GeoArea,
    m.Location,
    m.Route,
    m.Service,
    m.Ship,
    m.Sailing,
    m.EnRouteStop,
    m.ScheduledSailing,
    m.CurrentSailing,
])
