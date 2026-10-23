from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingCreateRequest,
    BookingListResponse,
    BookingResponse,
)
from app.models.notification import NotificationType
from app.services.notification_service import notification_service
from app.services.booking_service import booking_service
router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post(
    "",
    response_model = BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book tickets for an event")
async def create_booking(
    payload: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    booking = await booking_service.create_booking(db, data=payload, current_user=current_user)
    background_tasks.add_task(
        notification_service.send_background_notification,
        user_id=current_user.id,
        title="Booking Confirmed",
        message=f"You successfully booked {payload.ticket_count} ticket(s) for '{booking.event.title}'.",
        notification_type=NotificationType.BOOKING,
    )
    return booking


@router.get(
    "",
    response_model=BookingListResponse,
    summary="List current user's bookings"
)
async def list_my_bookings(
    skip:int = Query(default=0,ge=0),
    limit:int = Query(default=20,ge=1,le=100),
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items,total=await booking_service.list_user_bookings(db,current_user=current_user,skip=skip,limit=limit)
    return BookingListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )

@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Cancel a booking",
)
async def cancel_booking(
    booking_id:UUID,
    background_tasks:BackgroundTasks,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = await booking_service.cancel_booking(
        db, booking_id=booking_id, current_user=current_user
    )
    # Queue notification in the background
    background_tasks.add_task(
        notification_service.send_background_notification,
        user_id=booking.user_id,
        title="Booking Cancelled",
        message=f"Your booking for '{booking.event.title}' has been cancelled.",
        notification_type=NotificationType.BOOKING,
    )
    return booking
