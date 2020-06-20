from django.contrib.auth.models import Group, Permission


def riderGroupAdd(user):
    group, created = Group.objects.get_or_create(
        name="rider", defaults={"name": "rider"})
    if(created):
        permissions = Permission.objects.filter(
                codename__in=["view_order","change_order","view_rider","view_user"])
        group.permissions.set(permissions)
    user.groups.add(group)
