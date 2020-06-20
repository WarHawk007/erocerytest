from ...subshop import models

def resolve_subshops():
    return models.SubShop.objects.all()