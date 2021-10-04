from django.contrib import admin as a
from . import models as m

a.site.register([
    m.City,
    m.GeoArea,
    m.Terminal,
    m.Route,
    m.RouteInfo,
    m.Service,
    m.Ferry,
    m.Sailing,
    m.EnRouteStop,
    m.ScheduledSailing,
    m.CurrentSailing,
])
