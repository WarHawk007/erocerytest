import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command

from ...account.models import Address
from ...core.permissions import SubShopPermission
from ...subshop import models as subshop_models
from ...account import models as account_models
from ...core.error_codes import ShopErrorCode
from ...core.utils.url import validate_storefront_url
from ...site import models as site_models
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..core.enums import WeightUnitsEnum
from ..core.mutations import BaseMutation, ModelMutation
from ..core.types import Upload
from ..core.utils import validate_image_file
from ..core.types.common import ShopError
from ..decorators import one_of_permissions_required
from ..product.types import Collection
from ..utils import check_one_of_permissions
from .types import AuthorizationKey, AuthorizationKeyType, Shop, SubShop
from .utils import subShopSroup_add

class ShopSettingsInput(graphene.InputObjectType):
    header_text = graphene.String(description="Header text.")
    description = graphene.String(description="SEO description.")
    include_taxes_in_prices = graphene.Boolean(description="Include taxes in prices.")
    display_gross_prices = graphene.Boolean(
        description="Display prices with tax in store."
    )
    charge_taxes_on_shipping = graphene.Boolean(description="Charge taxes on shipping.")
    track_inventory_by_default = graphene.Boolean(
        description="Enable inventory tracking."
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit.")
    automatic_fulfillment_digital_products = graphene.Boolean(
        description="Enable automatic fulfillment for all digital products."
    )
    default_digital_max_downloads = graphene.Int(
        description="Default number of max downloads per digital content URL."
    )
    default_digital_url_valid_days = graphene.Int(
        description="Default number of days which digital content URL will be valid."
    )
    default_mail_sender_name = graphene.String(
        description="Default email sender's name."
    )
    default_mail_sender_address = graphene.String(
        description="Default email sender's address."
    )
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password."
    )


class SiteDomainInput(graphene.InputObjectType):
    domain = graphene.String(description="Domain name for shop.")
    name = graphene.String(description="Shop site name.")


class ShopSettingsUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = ShopSettingsInput(
            description="Fields required to update shop settings.", required=True
        )

    class Meta:
        description = "Updates shop settings."
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def clean_input(cls, _info, _instance, data):
        if data.get("customer_set_password_url"):
            try:
                validate_storefront_url(data["customer_set_password_url"])
            except ValidationError as error:
                raise ValidationError(
                    {"customer_set_password_url": error}, code=ShopErrorCode.INVALID
                )
        return data

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        for field_name, desired_value in cleaned_data.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        return instance

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = info.context.site.settings
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)
        instance.save()
        return ShopSettingsUpdate(shop=Shop())


class ShopAddressUpdate(BaseMutation, I18nMixin):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = AddressInput(description="Fields required to update shop address.")

    class Meta:
        description = (
            "Update the shop's address. If the `null` value is passed, the currently "
            "selected address will be deleted."
        )
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        site_settings = info.context.site.settings
        data = data.get("input")

        if data:
            if not site_settings.company_address:
                company_address = Address()
            else:
                company_address = site_settings.company_address
            company_address = cls.validate_address(data, company_address)
            company_address.save()
            site_settings.company_address = company_address
            site_settings.save(update_fields=["company_address"])
        else:
            if site_settings.company_address:
                site_settings.company_address.delete()
        return ShopAddressUpdate(shop=Shop())

class ShopBannerCreateInput(graphene.InputObjectType):
    images = graphene.List(Upload)
class ShopBannerCreate(BaseMutation):
    message = graphene.String()
    class Arguments:
        input = ShopBannerCreateInput(description="Fields required to update site.")

    class Meta:
        description = "Updates site domain of the shop."
        # permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data["input"]
        images = info.context.FILES
        for key in images:
            image = images[key]
            validate_image_file(image,"images")
            site_models.SiteBanner.objects.create(image=image)

        return ShopBannerCreate(message="Done")
class ShopDomainUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = SiteDomainInput(description="Fields required to update site.")

    class Meta:
        description = "Updates site domain of the shop."
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        site = info.context.site
        data = data.get("input")
        domain = data.get("domain")
        name = data.get("name")
        if domain is not None:
            site.domain = domain
        if name is not None:
            site.name = name
        cls.clean_instance(site)
        site.save()
        return ShopDomainUpdate(shop=Shop())


class ShopFetchTaxRates(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Meta:
        description = "Fetch tax rates."
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, _info):
        if not settings.VATLAYER_ACCESS_KEY:
            raise ValidationError(
                "Could not fetch tax rates. Make sure you have supplied a "
                "valid API Access Key.",
                code=ShopErrorCode.CANNOT_FETCH_TAX_RATES,
            )
        call_command("get_vat_rates")
        return ShopFetchTaxRates(shop=Shop())


class HomepageCollectionUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        collection = graphene.ID(description="Collection displayed on homepage.")

    class Meta:
        description = "Updates homepage collection of the shop."
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info, collection=None):
        new_collection = cls.get_node_or_error(
            info, collection, field="collection", only_type=Collection
        )
        site_settings = info.context.site.settings
        site_settings.homepage_collection = new_collection
        cls.clean_instance(site_settings)
        site_settings.save(update_fields=["homepage_collection"])
        return HomepageCollectionUpdate(shop=Shop())


class AuthorizationKeyInput(graphene.InputObjectType):
    key = graphene.String(
        required=True, description="Client authorization key (client ID)."
    )
    password = graphene.String(required=True, description="Client secret.")


class AuthorizationKeyAdd(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description="Newly added authorization key."
    )
    shop = graphene.Field(Shop, description="Updated shop.")

    class Meta:
        description = "Adds an authorization key."
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description="Type of an authorization key to add."
        )
        input = AuthorizationKeyInput(
            required=True, description="Fields required to create an authorization key."
        )

    @classmethod
    def perform_mutation(cls, _root, info, key_type, **data):
        if site_models.AuthorizationKey.objects.filter(name=key_type).exists():
            raise ValidationError(
                {
                    "key_type": ValidationError(
                        "Authorization key already exists.",
                        code=ShopErrorCode.ALREADY_EXISTS,
                    )
                }
            )

        site_settings = info.context.site.settings
        instance = site_models.AuthorizationKey(
            name=key_type, site_settings=site_settings, **data.get("input")
        )
        cls.clean_instance(instance)
        instance.save()
        return AuthorizationKeyAdd(authorization_key=instance, shop=Shop())


class AuthorizationKeyDelete(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description="Authorization key that was deleted."
    )
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description="Type of a key to delete."
        )

    class Meta:
        description = "Deletes an authorization key."
        permissions = ("site.manage_settings",)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info, key_type):
        try:
            site_settings = info.context.site.settings
            instance = site_models.AuthorizationKey.objects.get(
                name=key_type, site_settings=site_settings
            )
        except site_models.AuthorizationKey.DoesNotExist:
            raise ValidationError(
                {
                    "key_type": ValidationError(
                        "Couldn't resolve authorization key",
                        code=ShopErrorCode.NOT_FOUND,
                    )
                }
            )

        instance.delete()
        return AuthorizationKeyDelete(authorization_key=instance, shop=Shop())


class SubShopCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Sub Shop Name", required=True)
    city = graphene.String(description="City of Sub Shop", required=True)
    phone = graphene.String(description="Shop Admin Phone Number", required=True)
    password = graphene.String(description="Shop Admin Password", required=True)

class SubShopCreate(ModelMutation):
    class Arguments:
        input = SubShopCreateInput(
            description="Fields required to create a sub shop."
        )
    # @classmethod
    # def check_permissions(cls, context):
    #     return check_one_of_permissions(["subshop.manage_subshops","subshop.view_subshop"],context.user)
    
    class Meta:
        description = "Create A New Sub Shop"
        permissions = ("subshop.manage_subshops")
        model = subshop_models.SubShop
        error_type_class = ShopError
        error_type_field = "shop_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        user = account_models.User.objects.filter(phone=cleaned_input["phone"])
        if len(user)>0:    
            raise ValidationError({"phone":"User with phone already exsits "})
        return cleaned_input

    @classmethod
    def save(cls, root, info, cleaned_input):
        subshop = subshop_models.SubShop.objects.create(**cleaned_input)
        user = account_models.User.objects.create_user(password=cleaned_input["password"],phone=cleaned_input["phone"],is_staff=True,shopid=subshop)
        subShopSroup_add(user)
        return cls.success_response(subshop)
