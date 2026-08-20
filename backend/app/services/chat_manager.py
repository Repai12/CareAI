"""
services/chat_manager.py
---------------------------
In-memory WebSocket connection registry for Family Chat, one "room" per
patient. Deliberately in-memory, not a Redis pub/sub layer - this is a
single-process dev/demo deployment (same scale assumption the rest of
this project makes, e.g. the in-memory access-token design in
apiClient.ts), and a second process/worker isn't in scope here. If this
app ever runs behind multiple workers, broadcasts would need to move to
a shared pub/sub instead of this dict.
"""

import uuid
from typing import Dict, Set

from fastapi import WebSocket


class ChatConnectionManager:
    def __init__(self):
        self._rooms: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(self, patient_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        self._rooms.setdefault(patient_id, set()).add(websocket)

    def disconnect(self, patient_id: uuid.UUID, websocket: WebSocket):
        room = self._rooms.get(patient_id)
        if room is not None:
            room.discard(websocket)
            if not room:
                self._rooms.pop(patient_id, None)

    async def broadcast(self, patient_id: uuid.UUID, message: dict):
        room = self._rooms.get(patient_id)
        if not room:
            return
        dead = []
        for ws in room:
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 - a dead socket shouldn't break the rest of the room
                dead.append(ws)
        for ws in dead:
            room.discard(ws)


manager = ChatConnectionManager()
