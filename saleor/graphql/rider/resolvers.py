from ...rider import models

def resolve_rider():
    return models.Rider.objects.all()