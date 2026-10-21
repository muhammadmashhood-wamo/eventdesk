from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.event import (
    EventCreateRequest,
    EventFilterParams,
    EventListResponse,
    EventResponse,
    EventUpdateRequest,
)
from app.services.event_service import event_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    payload: EventCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    return await event_service.create_event(db, data=payload, organizer=current_user)


@router.get("", response_model=EventListResponse)
async def list_events(
    filters: EventFilterParams = Depends(), db: AsyncSession = Depends(get_db)
):
    items, total = await event_service.list_events(
        db, filters=filters, current_user=None
    )
    return EventListResponse(
        items=items, total=total, skip=filters.skip, limit=filters.limit
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await event_service.get_event(db, event_id=event_id, current_user=None)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    payload: EventUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    return await event_service.update_event(
        db, event_id=event_id, data=payload, current_user=current_user
    )


@router.post("/{event_id}/cancel", response_model=EventResponse)
async def cancel_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    return await event_service.cancel_event(
        db, event_id=event_id, current_user=current_user
    )
