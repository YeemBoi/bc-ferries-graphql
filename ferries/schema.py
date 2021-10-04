import graphene as g
from graphene_django.debug import DjangoDebug
import graphql_jwt as g_jwt

import core.schema
import sitemap.schema


class Query(core.schema.Query, sitemap.schema.Query, g.ObjectType):
    debug = g.Field(DjangoDebug, name='_debug')

class Mutation(g.ObjectType):
    token_auth      = g_jwt.ObtainJSONWebToken.Field()
    verify_token    = g_jwt.Verify.Field()
    refresh_token   = g_jwt.Refresh.Field()


schema = g.Schema(query=Query, mutation=Mutation)
