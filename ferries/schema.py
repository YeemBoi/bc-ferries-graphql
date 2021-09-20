import graphene as g
import graphql_jwt as g_jwt # type: ignore

import core.schema


class Query(core.schema.Query, g.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

class Mutation(g.ObjectType):
    token_auth = g_jwt.ObtainJSONWebToken.Field()
    verify_token = g_jwt.Verify.Field()
    refresh_token = g_jwt.Refresh.Field()


schema = g.Schema(query=Query, mutation=Mutation)
