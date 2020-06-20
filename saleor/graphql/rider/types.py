import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay
from graphene_django.types import DjangoObjectType
from ...rider import models as rider_models
from ..core.connection import CountableDjangoObjectType
from ..core.types.meta import MetadataObjectType
from ..core.fields import PrefetchingConnectionField, FilterInputConnectionField
from ..core.types import FilterInputObjectType
from ..core.enums import ReportingPeriod
from ..order.enums import OrderStatusFilter
from ..utils import filter_by_period
from ..order.filters import OrderFilter

class RiderOrderFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = OrderFilter

def filter_orders(qs, info, created, status):

    # filter orders by status
    if status is not None:
        if status == OrderStatusFilter.READY_TO_FULFILL:
            qs = qs.ready_to_fulfill()
        elif status == OrderStatusFilter.READY_TO_CAPTURE:
            qs = qs.ready_to_capture()
        elif status == OrderStatusFilter.FULFILLED:
            qs = qs.fullfilled()
        elif status == OrderStatusFilter.ASSIGNED:
            qs = qs.assigned()

    # filter orders by creation date
    if created is not None:
        qs = filter_by_period(qs, created, "created")

    return gql_optimizer.query(qs, info)

class Rider(MetadataObjectType, CountableDjangoObjectType):
    name = graphene.String(description="Rider Name", required=True)
    city = graphene.String(description="City of Rider", required=True)
    cnic = graphene.String(description="Cnic of Rider", required=True)
    shopid = graphene.String(description="Shop id of Rider", required=True)
    number = graphene.String(description="User-friendly number of an order.")
    # me = graphene.Field('saleor.graphql.account.types.User',description="Rider User Information")
    phone = graphene.String(description="Rider Phone", required=True)
    orders = FilterInputConnectionField(
        'saleor.graphql.order.types.Order',
        filter=RiderOrderFilterInput(description="Filtering options for orders."),
        created=graphene.Argument(
            ReportingPeriod, description="Filter orders from a selected timespan."
        ),
        status=graphene.Argument(
            OrderStatusFilter, description="Filter order by status."
        ),
        description="List of orders.",
    )

    @staticmethod
    def resolve_orders(root: rider_models.Rider, info, **kwargs,):
        viewer = info.context.user
        # if viewer.has_perm("order.manage_orders"):
        # print(f"==========={root.order_subshop.all()}==========")
        qs = root.rider.all()
        return filter_orders(qs,info,kwargs.get("created"),kwargs.get("status"))
    
    @staticmethod
    def resolve_phone(root: rider_models.Rider, info, **kwargs,):
        try:
            return root.admin_rider.phone
        except:
            return 0
    
    @staticmethod
    def resolve_number(root: rider_models.Rider, _info):
        return str(root.pk)
    
    class Meta:
        description = "Represents an order in Rider."
        model = rider_models.Rider
        interfaces = [relay.Node]
        only_fields = [
            "id",
            "name",
            "city",
            "cnic",
            "shopid"
            "created_at",
            "orders",
            "phone",
            "number"
        ]
