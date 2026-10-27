from uuid import UUID
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from app.core.config import settings
from app.core.websockets import manager
from app.core.security import decode_token
router = APIRouter(prefix="/ws", tags=["WebSockets"])

def get_user_id_from_token(token: str) -> UUID | None:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        sub: str = payload.get("sub")
        if not sub:
            return None
        return UUID(sub)
    except (JWTError, ValueError):
        return None


@router.websocket("/events/{event_id}")
async def websocket_event_tickets(websocket: WebSocket, event_id: UUID):
    await manager.connect_event(event_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_event(event_id, websocket)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
):
    user_id = get_user_id_from_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect_user(user_id,websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(user_id,websocket)
    
