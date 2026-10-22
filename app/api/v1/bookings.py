from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingCreateRequest,
    BookingListResponse,
    BookingResponse,
)
from app.services.booking_service import booking_service
router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post(
    "",
    response_model = BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book tickets for an event")
async def create_booking(
    payload: BookingCreateRequest,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    return await booking_service.create_booking(db,data=payload,current_user=current_user)

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
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await booking_service.cancel_booking(db,booking_id=booking_id,current_user=current_user)

