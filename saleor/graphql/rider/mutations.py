import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from ...rider import models as rider_models
from ...subshop import models as subshop_models
from ...account import models as account_models
from ..account.validation import isPhoneNumber, isCnic
from ..core.mutations import ModelMutation
from ..core.types.common import RiderError
from ..shop.types import SubShop
from .types import Rider
from .utils import riderGroupAdd


class RiderCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Rider Name", required=True)
    city = graphene.String(description="City of Rider", required=True)
    cnic = graphene.String(description="Rider cnic", required=True)
    shopid = graphene.String(description="Enter shop id", required=True)
    phone = graphene.String(description="Rider Phone Number", required=True)
    password = graphene.String(description="Rider Password", required=True)


class RiderCreate(ModelMutation):
    class Arguments:
        input = RiderCreateInput(
            description="Fields required to create a rider.", required=True
        )

    class Meta:
        description = "Create A New Rider"
        permissions = ("rider.manage_riders",)
        model = rider_models.Rider
        error_type_class = RiderError
        error_type_field = "rider_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        data = data["input"]
        isPhoneNumber(data["phone"])
        isCnic(data["cnic"])
        user = account_models.User.objects.filter(phone=data["phone"])
        if len(user) > 0 and user[0].riderid:
            raise ValidationError({"phone": "User with phone already is a rider"})
        shopid = graphene.Node.get_node_from_global_id(
            info, data["shopid"], SubShop)
        rider = rider_models.Rider.objects.create(
            name=data["name"], city=data["city"], cnic=data["cnic"], shopid=shopid)
        if len(user) > 0:
            user.update(riderid=rider, is_rider=True)
            user = user[0]
        else:
            user = account_models.User.objects.create_user(
                password=data["password"], phone=data["phone"], is_active=True, phone_verified=True, riderid=rider, is_rider=True)
            riderGroupAdd(user)
        return cls.success_response(rider)
