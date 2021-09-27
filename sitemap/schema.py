from django.conf import settings

from . import models as m
from common import graphene_utils as gu

import graphene as g
import graphene_django as gd
import django_filters as df



class SitemapNode(gd.DjangoObjectType):
    class Meta:
        model = m.Sitemap
        filter_fields = {
            'parent_sitemap': [],
            'index_sitemap': [],
            'url': settings.DEFAULT_STRING_LOOKUPS,
            'sitemap_type': ['exact', 'iexact'],
            'is_index': ['exact'],
            'is_invalid': ['exact'],
            'is_invalid': ['exact'],
            'invalid_reason': settings.DEFAULT_STRING_LOOKUPS,
        }
        interfaces = (g.relay.Node, )

class PageNode(gd.DjangoObjectType):
    change_frequency = g.String()
    class Meta:
        model = m.Page
        filter_fields = {
            'sitemap': [],
            'change_frequency': [],
            'url': settings.DEFAULT_STRING_LOOKUPS,
            'priority': settings.DEFAULT_RANGE_LOOKUPS,
            'last_modified': settings.DEFAULT_DATETIME_LOOKUPS,
            **gu.fk_filters(SitemapNode, 'sitemap'),

        }
        interfaces = (g.relay.Node, )

class Query(g.ObjectType):
    sitemap,    all_sitemaps    = gu.make_filter_relay(SitemapNode)
    page,       all_pages       = gu.make_filter_relay(PageNode)
