from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    def _active_filter(self):
        return [Event.is_deleted.is_(False)]

    async def get_by_id_active(self, db: AsyncSession, event_id: UUID) -> Event | None:
        stmt = (
            select(Event)
            .options(selectinload(Event.organizer))
            .where(Event.id == event_id, Event.is_deleted.is_(False))
        )
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
        tag: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str | None = None,
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
        if tag:
            filters.append(Event.tags.contains([tag]))
        if min_price is not None:
            filters.append(Event.ticket_price >= min_price)
        if max_price is not None:
            filters.append(Event.ticket_price <= max_price)
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

        order_clause = Event.event_date.asc()
        if sort_by == "date_desc":
            order_clause = Event.event_date.desc()
        elif sort_by == "date_asc":
            order_clause = Event.event_date.asc()
        elif sort_by == "price_asc":
            order_clause = Event.ticket_price.asc()
        elif sort_by == "price_desc":
            order_clause = Event.ticket_price.desc()
        elif sort_by == "created_at_desc":
            order_clause = Event.created_at.desc()
        elif sort_by == "title_asc":
            order_clause = Event.title.asc()

        rows_stmt = (
            select(Event)
            .options(selectinload(Event.organizer))
            .where(and_(*filters))
            .order_by(order_clause)
            .offset(skip)
            .limit(limit)
        )
        rows = list((await db.execute(rows_stmt)).scalars().all())
        return rows, total

    async def list_categories(self, db: AsyncSession) -> list[str]:
        stmt = (
            select(Event.category)
            .where(Event.is_deleted.is_(False), Event.category.is_not(None))
            .distinct()
        )
        result = await db.execute(stmt)
        return [c for c in result.scalars().all() if c and c.strip()]

    async def get_by_organizer(
        self, db: AsyncSession, organizer_id: UUID
    ) -> list[Event]:
        stmt = (
            select(Event)
            .options(selectinload(Event.organizer))
            .where(Event.organizer_id == organizer_id, Event.is_deleted.is_(False))
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
