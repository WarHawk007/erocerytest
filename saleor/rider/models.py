from django.db import models
from django.utils.translation import pgettext_lazy

from ..core.models import (
    ModelWithMetadata,
)
from ..subshop.models import SubShop


class RiderQuerySet(models.QuerySet):
    def create(self, **kwargs):
        return super().create(name=kwargs['name'],city=kwargs['city'],cnic=kwargs['cnic'],shopid=kwargs['shopid'])

class Rider(ModelWithMetadata):
    name = models.CharField(blank=False,max_length=128)
    city = models.CharField(blank=False,max_length=128)
    cnic = models.CharField(blank=False,max_length=128)
    shopid = models.ForeignKey(
        SubShop, related_name="rider_subshop", null=True, on_delete=models.SET_NULL,blank=None
    )
    isonline = models.BooleanField(default=False)
    channel = models.CharField(blank=True,max_length=100)
    created_at = models.DateTimeField(auto_now=True, null=True)
    objects = RiderQuerySet.as_manager()

    class Meta:
        app_label = "rider"
        ordering = ("id",)
        permissions = (
            (
                "manage_riders",
                pgettext_lazy("Permission description", "Manage riders"),
            ),
        )