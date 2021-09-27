from django.conf import settings
from django.db import models as m
from urllib.parse import urlparse, ParseResult
from usp.objects.page import SitemapPageChangeFrequency as SmPCF
from datetime import timedelta

SITEMAP_TYPE_CHOICES = [
    ('ROBO', 'robots.txt'),
    ('ATOM', 'RSS 0.3 / 1.0'),
    ('RSS',  'RSS 2.0'),
    ('TEXT', 'Plain text'),
    ('XML',  'XML'),
]

SITEMAP_PCF_DURATIONS = {
    SmPCF.ALWAYS.name:  timedelta(seconds=settings.SCRAPER_PAUSE_SECS),
    SmPCF.DAILY.name:   timedelta(days=1),
    SmPCF.HOURLY.name:  timedelta(hours=1),
    SmPCF.MONTHLY.name: timedelta(days=30),
    SmPCF.NEVER.name:   None,
    SmPCF.WEEKLY.name:  timedelta(days=7),
    SmPCF.YEARLY.name:  timedelta(days=365.24),
}


class PageChangeFrequency(m.Model):
    value = m.CharField(max_length=31, unique=True)
    name = m.CharField(max_length=31, unique=True)
    duration_rep = m.DurationField(null=True)

    def __str__(self) -> str:
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.duration_rep:
            self.duration_rep = SITEMAP_PCF_DURATIONS.get(self.name)
        super().save(*args, **kwargs)


class Sitemap(m.Model):
    parent_sitemap = m.ForeignKey('self', null=True, on_delete=m.SET_NULL, related_name='sub_sitemaps')
    index_sitemap = m.ForeignKey('self', null=True, on_delete=m.SET_NULL, related_name='all_sitemaps')
    url = m.URLField()
    sitemap_type = m.CharField(null=True, max_length=4, choices=SITEMAP_TYPE_CHOICES)
    is_index = m.BooleanField()
    is_invalid = m.BooleanField()
    invalid_reason = m.CharField(max_length=511, null=True)

    def parsed_url(self) -> ParseResult:
        return urlparse(self.url)

    def __str__(self) -> str:
        return self.url


class Page(m.Model):
    sitemap = m.ForeignKey(Sitemap, null=True, on_delete=m.CASCADE, related_name='pages')
    change_frequency = m.ForeignKey(PageChangeFrequency, on_delete=m.CASCADE)
    url = m.URLField()
    priority = m.FloatField()
    last_modified = m.DateTimeField(null=True)

    def parsed_url(self) -> ParseResult:
        return urlparse(self.url)
    
    def __str__(self) -> str:
        return self.url
