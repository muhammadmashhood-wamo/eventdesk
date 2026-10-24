from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.booking import Booking, BookingStatus
from app.models.event import Event
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    model = Booking
    
    async def get_by_id_active(self, db: AsyncSession, booking_id: UUID) -> Booking | None:
        stmt = (
            select(Booking)
            .options(selectinload(Booking.event).selectinload(Event.organizer))
            .where(Booking.id == booking_id, Booking.is_deleted.is_(False))
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def get_by_id_active_for_update(
        self, db: AsyncSession, booking_id: UUID
    ) -> Booking | None:
        stmt = (
            select(Booking)
            .options(selectinload(Booking.event).selectinload(Event.organizer))
            .where(Booking.id == booking_id, Booking.is_deleted.is_(False))
            .with_for_update()
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def list_user_bookings(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Booking], int]:

        filters = [Booking.user_id == user_id, Booking.is_deleted.is_(False)]

        count_stmt = select(func.count()).select_from(Booking).where(*filters)
        total = (await db.execute(count_stmt)).scalar_one()
        row_stmt = (
            select(Booking)
            .options(selectinload(Booking.event).selectinload(Event.organizer))
            .where(*filters)
            .order_by(Booking.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        rows = list((await db.execute(row_stmt)).scalars().all())

        return rows, total

    async def has_confirmed_booking(
        self, db: AsyncSession, *, user_id: UUID, event_id: UUID
    ) -> bool:
        stmt = select(func.count()).select_from(Booking).where(
            Booking.user_id == user_id,
            Booking.event_id == event_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.is_deleted.is_(False),
        )
        count = (await db.execute(stmt)).scalar_one()
        return count > 0


booking_repository = BookingRepository()