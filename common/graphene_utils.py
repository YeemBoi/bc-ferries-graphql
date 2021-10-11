from django.conf import settings
from typing import NamedTuple

import graphene as g
import graphene_django as gd
import graphene_django.filter as gdf
from graphene.relay.node import NodeField

class FilterRelay(NamedTuple):
    node: NodeField
    connection: gdf.DjangoFilterConnectionField

def make_filter_relay(node_class: gd.DjangoObjectType) -> FilterRelay:
    return FilterRelay(
        node = g.relay.Node.Field(node_class),
        connection = gdf.DjangoFilterConnectionField(node_class),
    )

def lookups(obj_type) -> list[str]:
    return settings.DEFAULT_LOOKUPS[obj_type]

def fk_filters(rel_class: gd.DjangoObjectType, rel_name: str) -> dict[str, list[str]]:
    newFields = dict()
    for field, filters in rel_class._meta.filter_fields.items():
        if len(filters):
            newFields['__'.join([rel_name, field])] = filters
    return newFields
