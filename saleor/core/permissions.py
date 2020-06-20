from enum import Enum

from django.contrib.auth.models import Permission


class BasePermissionEnum(Enum):
    @property
    def codename(self):
        return self.value.split(".")[1]


class AccountPermissions(BasePermissionEnum):
    MANAGE_USERS = "account.manage_users"
    MANAGE_STAFF = "account.manage_staff"
    MANAGE_SERVICE_ACCOUNTS = "account.manage_service_accounts"
    VIEW_USER = "account.view_user"


class DiscountPermissions(BasePermissionEnum):
    MANAGE_DISCOUNTS = "discount.manage_discounts"


class ExtensionsPermissions(BasePermissionEnum):
    MANAGE_PLUGINS = "extensions.manage_plugins"


class GiftcardPermissions(BasePermissionEnum):
    MANAGE_GIFT_CARD = "giftcard.manage_gift_card"


class MenuPermissions(BasePermissionEnum):
    MANAGE_MENUS = "menu.manage_menus"


class CheckoutPermissions(BasePermissionEnum):
    MANAGE_CHECKOUTS = "checkout.manage_checkouts"


class OrderPermissions(BasePermissionEnum):
    MANAGE_ORDERS = "order.manage_orders"
    ASSIGN_ORDER = "order.assign_order"
    VIEW_ORDER = "order.view_order"
    CHANGE_ORDER = "order.change_order"


class PagePermissions(BasePermissionEnum):
    MANAGE_PAGES = "page.manage_pages"


class ProductPermissions(BasePermissionEnum):
    MANAGE_PRODUCTS = "product.manage_products"
    VIEW_PRODUCT = "product.view_product"

class RiderPermission(BasePermissionEnum):
    VIEW_RIDER = "rider.view_rider"
    MANAGE_RIDERS = "rider.manage_riders"

class ShippingPermissions(BasePermissionEnum):
    MANAGE_SHIPPING = "shipping.manage_shipping"

class SitePermissions(BasePermissionEnum):
    MANAGE_SETTINGS = "site.manage_settings"
    MANAGE_TRANSLATIONS = "site.manage_translations"

class SubShopPermission(BasePermissionEnum):
    MANAGE_SUBSHOPS = "subshop.manage_subshops"
    VIEW_SUBSHOP = "subshop.view_subshop"

class WebhookPermissions(BasePermissionEnum):
    MANAGE_WEBHOOKS = "webhook.manage_webhooks"


PERMISSIONS_ENUMS = [
    AccountPermissions,
    DiscountPermissions,
    ExtensionsPermissions,
    GiftcardPermissions,
    MenuPermissions,
    OrderPermissions,
    PagePermissions,
    ProductPermissions,
    RiderPermission,
    ShippingPermissions,
    SitePermissions,
    SubShopPermission,
    WebhookPermissions,
    CheckoutPermissions,
]


def split_permission_codename(permissions):
    return [permission.split(".")[1] for permission in permissions]


def get_permissions_codename():
    permissions_values = [
        enum.codename
        for permission_enum in PERMISSIONS_ENUMS
        for enum in permission_enum
    ]
    return permissions_values


def get_permissions_enum_list():
    permissions_list = [
        (enum.name, enum.value)
        for permission_enum in PERMISSIONS_ENUMS
        for enum in permission_enum
    ]
    return permissions_list


def get_permissions(permissions=None):
    if permissions is None:
        codenames = get_permissions_codename()
    else:
        codenames = split_permission_codename(permissions)
    return (
        Permission.objects.filter(codename__in=codenames)
        .prefetch_related("content_type")
        .order_by("codename")
    )
