from datetime import datetime
from . import models as m
import graphene as g
import graphene_django as gd
from common import graphene_utils as u


class SitemapNode(gd.DjangoObjectType):
    class Meta:
        model = m.Sitemap
        filter_fields = {
            'url': u.lookups(str),
            'sitemap_type': ['exact', 'iexact'],
            'is_index': u.lookups(bool),
            'is_invalid': u.lookups(bool),
        }
        interfaces = (g.relay.Node, )

class PageNode(gd.DjangoObjectType):
    change_frequency = g.String()
    class Meta:
        model = m.Page
        filter_fields = {
            'url': u.lookups(str),
            'priority': u.lookups(int),
            'last_modified': u.lookups(datetime),
            **u.fk_filters(SitemapNode, 'sitemap'),

        }
        interfaces = (g.relay.Node, )

class Query(g.ObjectType):
    sitemap,    all_sitemaps    = u.make_filter_relay(SitemapNode)
    page,       all_pages       = u.make_filter_relay(PageNode)
