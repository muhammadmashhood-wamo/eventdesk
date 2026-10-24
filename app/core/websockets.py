from collections import defaultdict
from uuid import UUID
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.user_connections: dict[UUID,list[WebSocket]] = defaultdict(list)

        self.event_connections: dict[UUID,list[WebSocket]] = defaultdict(list)

    async def connect_user(self,user_id:UUID,websocket:WebSocket):
        await websocket.accept()
        self.user_connections[user_id].append(websocket)

    def disconnect_user(self, user_id: UUID, websocket: WebSocket) -> None:
        if websocket in self.user_connections.get(user_id, []):
            self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                self.user_connections.pop(user_id, None)

    async def send_to_user(self, user_id: UUID, message: dict) -> None:
        sockets = list(self.user_connections.get(user_id, []))
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect_user(user_id, ws)

    async def connect_event(self, event_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.event_connections[event_id].append(websocket)

    def disconnect_event(self, event_id: UUID, websocket: WebSocket) -> None:
        if websocket in self.event_connections.get(event_id, []):
            self.event_connections[event_id].remove(websocket)
            if not self.event_connections[event_id]:
                self.event_connections.pop(event_id, None)

    async def broadcast_event_ticket_update(
        self, event_id: UUID, available_tickets: int
    ) -> None:
        sockets = list(self.event_connections.get(event_id, []))
        payload = {
            "type": "TICKET_UPDATE",
            "event_id": str(event_id),
            "available_tickets": available_tickets,
        }
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect_event(event_id, ws)

manager = ConnectionManager()