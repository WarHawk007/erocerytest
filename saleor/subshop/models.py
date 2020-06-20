from django.db import models
from django.utils.translation import pgettext_lazy
from ..core.models import (
    ModelWithMetadata,
)
from ..core.permissions import (
    SubShopPermission
)

class SubShopQuerySet(models.QuerySet):
    def create(self, **kwargs):
        return super().create(name=kwargs['name'],city=kwargs['city'])

class SubShop(ModelWithMetadata):
    name = models.CharField(blank=False,max_length=128)
    city = models.CharField(blank=False,max_length=128)
    created_at = models.DateTimeField(auto_now=True, null=True)
    objects = SubShopQuerySet.as_manager()

    class Meta:
        app_label = "subshop"
        ordering = ("name",)
        permissions = (
            (
                SubShopPermission.MANAGE_SUBSHOPS.codename,
                pgettext_lazy("Permission description", "Manage_subshops"),
            ),
        )