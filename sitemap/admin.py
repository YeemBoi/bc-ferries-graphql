from django.contrib import admin as a
from . import models as m

a.site.register([
    m.PageChangeFrequency,
    m.Sitemap,
    m.Page,
])
