from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: bool | None = Query(None, description="Filter by read status"),
    type: NotificationType | None = Query(None, description="Filter by notification type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total, unread_count = await notification_service.list_notifications(
        db,
        current_user=current_user,
        is_read=is_read,
        notification_type=type,
        skip=skip,
        limit=limit,
    )
    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.set_read_status(
        db,
        notification_id=notification_id,
        current_user=current_user,
        is_read=True,
    )


@router.patch("/{notification_id}/unread", response_model=NotificationResponse)
async def mark_as_unread(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.set_read_status(
        db,
        notification_id=notification_id,
        current_user=current_user,
        is_read=False,
    )


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.mark_all_notifications_as_read(
        db, current_user=current_user
    )
    return {"message": f"{count} notifications marked as read"}
