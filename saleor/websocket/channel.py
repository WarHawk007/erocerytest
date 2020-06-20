from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

def send(channel_name,message):
    async_to_sync(channel_layer.send)(channel_name, {
            "type": "new.order",
            "message": message,
        })

def send_admin(channel_name,message):
    async_to_sync(channel_layer.send)(channel_name, {
            "type": "rider.reject",
            "message": message,
        })