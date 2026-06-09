import asyncio
from contextlib import suppress

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.matches import realtime


class MatchRealtimeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.public_match_id = self.scope["url_route"]["kwargs"]["match_id"]
        try:
            self.group_name = realtime.match_group_name(public_match_id=self.public_match_id)
            raw_access_token = realtime.access_token_from_scope(scope=self.scope)
            match = await database_sync_to_async(realtime.current_match_snapshot)(
                raw_access_token=raw_access_token,
                public_match_id=self.public_match_id,
            )
        except ValueError:
            await self.close(code=4404)
            return
        except ApiErrorResponseException as exc:
            await self.close(code=realtime.websocket_close_code_for_error(exc))
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.heartbeat_task = asyncio.create_task(self._send_heartbeat())
        await self.send_json(realtime.build_match_snapshot_event(match=match))

    async def disconnect(self, _close_code):
        heartbeat_task = getattr(self, "heartbeat_task", None)
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

        group_name = getattr(self, "group_name", None)
        if group_name is None:
            return
        await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, _content, **_kwargs):
        await self.send_json(
            realtime.build_error_event(
                code="WEBSOCKET_READ_ONLY",
                message="state-changing actions must use REST API",
            )
        )

    async def match_event(self, event):
        await self.send_json(event["payload"])

    async def _send_heartbeat(self):
        while True:
            await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_SECONDS)
            await self.send_json({"type": realtime.EVENT_HEARTBEAT})
