import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from ..account.models import User


class RiderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        self.rider_logout(self.channel_name)
        self.admin_logout(self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data["type"] == "rider.login":
            self.rider_login(data, self.channel_name)
        elif data["type"] == "admin.login":
            self.admin_login(data, self.channel_name)

    async def new_order(self, event):
        print(self.channel_name)
        await self.send_json({"message": event["message"]})
    
    async def rider_reject(self, event):
        print(self.channel_name)
        await self.send_json({"message": event["message"]})

    def rider_login(self, data, channel):
        try:
            phone = data["payload"]["rider"]
            user = User.objects.get(phone=phone)
            user.riderid.isonline = True
            user.riderid.channel = channel
            user.riderid.save()
            self.send_json({"message":"registered"})
        except:
            print("No Rider")

    def rider_logout(self, channel):
        try:
            user = User.objects.get(riderid__channel=channel)
            user.riderid.isonline = False
            user.riderid.channel = ""
            user.riderid.save()
            self.send_json({"message":"Un Registered"})
        except:
            print("No Rider")
    
    def admin_login(self, data, channel):
        try:
            phone = data["payload"]["admin"]
            user = User.objects.get(phone=phone)
            user.channel = channel
            user.save()
            self.send_json({"message":"registered"})
        except:
            print("No Admin")

    def admin_logout(self, channel):
        try:
            user = User.objects.get(channel=channel)
            user.channel = ""
            user.save()
            self.send_json({"message":"Un Registered"})
        except:
            print("No Admin")