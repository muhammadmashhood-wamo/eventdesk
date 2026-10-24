from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import Booking, BookingStatus
from app.models.event import EventStatus
from app.models.user import User, UserRole
from app.repositories.booking_repository import booking_repository
from app.repositories.event_repository import event_repository
from app.schemas.booking import BookingCreateRequest

class BookingService:
    async def create_booking(
        self,
        db: AsyncSession,
        *,
        data: BookingCreateRequest,
        current_user: User,

    )-> Booking:
        event = await event_repository.get_by_id_for_update(db,data.event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        if event.status != EventStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot book tickets for an event with status '{event.status.value}'",
            )
        
        current_time = datetime.now(timezone.utc)
        event_time = event.event_date if event.event_date.tzinfo else event.event_date.replace(tzinfo=timezone.utc)
        if event_time <= current_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book tickets for an event that has already passed",
            )

        if event.available_tickets < data.ticket_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough tickets available. Only {event.available_tickets} left.",
            )
        
        event.available_tickets -= data.ticket_count

        booking = Booking(
            user_id = current_user.id,
            event_id = event.id,
            ticket_count = data.ticket_count,
            status = BookingStatus.CONFIRMED,
        )
        await booking_repository.create(db,booking)
        booking_with_event = await booking_repository.get_by_id_active(db,booking.id)

        return booking_with_event or booking
    
    async def list_user_bookings(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        ) -> tuple[list[Booking],int]:
        return await booking_repository.list_user_bookings(
            db, user_id = current_user.id, skip = skip, limit = limit
        )

    async def cancel_booking(
        self,
        db: AsyncSession,
        *,
        booking_id: UUID,
        current_user: User,
        ) -> Booking:
        return await self._change_booking_state(
            db,
            booking_id=booking_id,
            current_user=current_user,
            soft_delete=False,
        )

    async def delete_booking(
        self,
        db: AsyncSession,
        *,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        return await self._change_booking_state(
            db,
            booking_id=booking_id,
            current_user=current_user,
            soft_delete=True,
        )

    async def _change_booking_state(
        self,
        db: AsyncSession,
        *,
        booking_id: UUID,
        current_user: User,
        soft_delete: bool,
    ) -> Booking:
        booking = await booking_repository.get_by_id_active_for_update(db,booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )
        if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own bookings",
            )
        if booking.status == BookingStatus.CANCELLED and not soft_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled",
            )

        if booking.status == BookingStatus.CONFIRMED:
            event = await event_repository.get_by_id_for_update(db,booking.event_id)
            if event:
                event.available_tickets += booking.ticket_count

        booking.status = BookingStatus.CANCELLED
        booking.is_deleted = soft_delete
        await booking_repository.update(db, booking)
        if soft_delete:
            return booking
        updated_booking = await booking_repository.get_by_id_active(db, booking.id)
        return updated_booking or booking

booking_service = BookingService()



        