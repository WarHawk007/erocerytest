from django.contrib.auth.models import Group, Permission


def subShopSroup_add(user):
    group, created = Group.objects.get_or_create(
        name="subshop", defaults={"name": "subshop"})
    if(created):
        permissions = Permission.objects.filter(
                codename__in=["view_subshop", "assign_order","manage_staff","manage_users", "manage_orders", "view_rider", "view_product"])
        group.permissions.set(permissions)
    user.groups.add(group)
