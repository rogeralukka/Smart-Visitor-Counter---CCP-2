"""
Event broadcaster for Server-Sent Events (SSE).
Enables real-time push notifications from backend to the visitor counter dashboard.
"""

import asyncio
import json
from typing import Set

class EventBroadcaster:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    async def broadcast(self, event_type: str, data: dict):
        if not self._subscribers:
            return
        msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        for q in list(self._subscribers):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

    def broadcast_sync(self, event_type: str, data: dict):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(event_type, data))
        except RuntimeError:
            pass

broadcaster = EventBroadcaster()
