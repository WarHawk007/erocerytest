import graphene

from .mutations import (
    RiderCreate
)
from .resolvers import (
    resolve_rider
)
from .types import Rider


class RiderQueries(graphene.ObjectType):
    rider = graphene.Field(Rider, id=graphene.ID(
    ), description="Return information about the rider")
    riders = graphene.List(
        Rider, description="Return information about the riders")

    def resolve_riders(self, info):
        return resolve_rider()
    
    def resolve_rider(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Rider)


class RiderMutations(graphene.ObjectType):
    rider_create = RiderCreate.Field()