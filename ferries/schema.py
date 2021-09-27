import graphene as g
import graphql_jwt as g_jwt

import core.schema
import sitemap.schema


class Query(core.schema.Query, sitemap.schema.Query, g.ObjectType):
    pass

class Mutation(g.ObjectType):
    token_auth      = g_jwt.ObtainJSONWebToken.Field()
    verify_token    = g_jwt.Verify.Field()
    refresh_token   = g_jwt.Refresh.Field()


schema = g.Schema(query=Query, mutation=Mutation)
