import graphene

from ..decorators import permission_required,one_of_permissions_required
from ..translations.mutations import ShopSettingsTranslate
from .mutations import (
    AuthorizationKeyAdd,
    AuthorizationKeyDelete,
    HomepageCollectionUpdate,
    ShopAddressUpdate,
    ShopDomainUpdate,
    ShopFetchTaxRates,
    ShopSettingsUpdate,
    SubShopCreate
)
from .resolvers import (
    resolve_subshops
)
from .types import Shop, SubShop


class ShopQueries(graphene.ObjectType):
    shop = graphene.Field(Shop, description="Return information about the shop.")
    subshop = graphene.Field(SubShop, id=graphene.ID(
    ), description="Return information about the sub shop")
    subshops = graphene.List(
        SubShop, description="Return information about the sub shops")

    def resolve_shop(self, _info):
        return Shop()

    # @one_of_permissions_required(["subshop.view_subshop","subshop.manage_subshops"])
    def resolve_subshops(self, info):
        return resolve_subshops()
    
    @one_of_permissions_required(["subshop.view_subshop","subshop.manage_subshops"])
    def resolve_subshop(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, SubShop)


class ShopMutations(graphene.ObjectType):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

    homepage_collection_update = HomepageCollectionUpdate.Field()
    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    shop_fetch_tax_rates = ShopFetchTaxRates.Field()
    shop_settings_translate = ShopSettingsTranslate.Field()
    shop_address_update = ShopAddressUpdate.Field()
    sub_shop_create = SubShopCreate.Field()
