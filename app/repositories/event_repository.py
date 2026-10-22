from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    def _active_filter(self):
        return [Event.is_deleted.is_(False)]

    async def get_by_id_active(self, db: AsyncSession, event_id: UUID) -> Event | None:
        stmt = select(Event).where(Event.id == event_id, Event.is_deleted.is_(False))
        return (await db.execute(stmt)).scalar_one_or_none()

    async def list_events(
        self,
        db: AsyncSession,
        *,
        skip=0,
        limit=20,
        status: EventStatus | None = None,
        category: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        organizer_id: UUID | None = None,
    ) -> tuple[list[Event], int]:
        filters = self._active_filter()
        if status:
            filters.append(Event.status == status)
        if category:
            filters.append(Event.category == category)
        if organizer_id:
            filters.append(Event.organizer_id == organizer_id)
        if date_from:
            filters.append(Event.event_date >= date_from)
        if date_to:
            filters.append(Event.event_date <= date_to)
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Event.title.ilike(term),
                    Event.description.ilike(term),
                    Event.venue.ilike(term),
                )
            )
        total = (
            await db.execute(
                select(func.count()).select_from(Event).where(and_(*filters))
            )
        ).scalar_one()
        rows_stmt = (
            select(Event)
            .where(and_(*filters))
            .order_by(Event.event_date.asc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await db.execute(rows_stmt)).scalars().all())
        return rows, total

    async def get_by_organizer(
        self, db: AsyncSession, organizer_id: UUID
    ) -> list[Event]:
        stmt = select(Event).where(
            Event.organizer_id == organizer_id, Event.is_deleted.is_(False)
        )
        return list((await db.execute(stmt)).scalars().all())


    async def get_by_id_for_update(self, db: AsyncSession, event_id: UUID) -> Event | None:
        stmt = (
            select(Event)
            .where(Event.id == event_id, Event.is_deleted.is_(False))
            .with_for_update()
        )
        return (await db.execute(stmt)).scalar_one_or_none()


event_repository = EventRepository()
