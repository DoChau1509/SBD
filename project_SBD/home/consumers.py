import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .realtime import STAFF_MAP_GROUP


class StaffMapConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not (
            user.is_staff or user.is_superuser
        ):
            await self.close()
            return

        await self.channel_layer.group_add(STAFF_MAP_GROUP, self.channel_name)
        await self.accept()
        await self.send_snapshot()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(STAFF_MAP_GROUP, self.channel_name)

    async def staff_map_changed(self, event):
        await self.send_snapshot()

    async def send_snapshot(self):
        snapshot = await self.get_snapshot()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "staff_map_snapshot",
                    "snapshot": snapshot,
                }
            )
        )

    @database_sync_to_async
    def get_snapshot(self):
        from .views import _serialize_staff_map

        return _serialize_staff_map()
