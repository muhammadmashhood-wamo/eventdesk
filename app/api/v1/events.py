from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.event import (
    EventCreateRequest,
    EventFilterParams,
    EventListResponse,
    EventResponse,
    EventStatsResponse,
    EventUpdateRequest,
)
from app.services.audit_service import audit_service
from app.services.event_service import event_service
from app.services.notification_service import notification_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    payload: EventCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    event = await event_service.create_event(db, data=payload, organizer=current_user)
    background_tasks.add_task(
        audit_service.log_background,
        user_id=current_user.id,
        action="EVENT_CREATED",
        details=f"Created event '{event.title}' (ID: {event.id})",
    )
    return event


@router.get("", response_model=EventListResponse)
async def list_events(
    filters: EventFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    items, total = await event_service.list_events(
        db, filters=filters, current_user=current_user
    )
    return EventListResponse(
        items=items, total=total, skip=filters.skip, limit=filters.limit
    )


@router.get("/categories", response_model=list[str])
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    return await event_service.list_categories(db)


@router.get("/stats", response_model=EventStatsResponse)
@router.get("/dashboard", response_model=EventStatsResponse)
async def get_event_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    return await event_service.get_stats(db, current_user=current_user)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return await event_service.get_event(db, event_id=event_id, current_user=current_user)


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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    cancelled_event = await event_service.cancel_event(
        db, event_id=event_id, current_user=current_user
    )
    background_tasks.add_task(
        notification_service.notify_event_cancelled,
        event_id=cancelled_event.id,
        event_title=cancelled_event.title,
    )
    background_tasks.add_task(
        audit_service.log_background,
        user_id=current_user.id,
        action="EVENT_CANCELLED",
        details=f"Cancelled event '{cancelled_event.title}' (ID: {cancelled_event.id})",
    )
    return cancelled_event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANIZER])),
):
    deleted_event = await event_service.delete_event(
        db, event_id=event_id, current_user=current_user
    )
    background_tasks.add_task(
        audit_service.log_background,
        user_id=current_user.id,
        action="EVENT_DELETED",
        details=f"Deleted event '{deleted_event.title}' (ID: {deleted_event.id})",
    )
