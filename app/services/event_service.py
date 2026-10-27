from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.event import Event, EventStatus
from app.models.user import User, UserRole
from app.repositories.event_repository import event_repository
from app.schemas.event import (
    EventCreateRequest,
    EventFilterParams,
    EventStatsResponse,
    EventUpdateRequest,
)


class EventService:
    async def create_event(
        self, db: AsyncSession, *, data: EventCreateRequest, organizer: User
    ) -> Event:
        event = Event(
            organizer_id=organizer.id,
            title=data.title,
            description=data.description,
            venue=data.venue,
            event_date=data.event_date,
            ticket_price=data.ticket_price,
            total_tickets=data.total_tickets,
            available_tickets=data.total_tickets,
            status=data.status,
            category=data.category,
            tags=data.tags,
        )
        created = await event_repository.create(db, obj=event)
        await db.commit()
        return await event_repository.get_by_id_active(db, created.id) or created

    async def get_event(
        self, db: AsyncSession, *, event_id: UUID, current_user: User | None = None
    ) -> Event:
        event = await event_repository.get_by_id_active(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        if event.status != EventStatus.PUBLISHED:
            if not current_user or (
                current_user.role != UserRole.ADMIN
                and current_user.id != event.organizer_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Event not found",
                )
        return event

    async def list_events(
        self,
        db: AsyncSession,
        *,
        filters: EventFilterParams,
        current_user: User | None = None,
    ) -> tuple[list[Event], int]:
        effective_status = filters.status
        effective_organizer_id = filters.organizer_id

        if not current_user or current_user.role == UserRole.ATTENDEE:
            effective_status = EventStatus.PUBLISHED
        elif current_user.role == UserRole.ADMIN:
            effective_status = filters.status
        elif current_user.role == UserRole.ORGANIZER:
            if filters.organizer_id == current_user.id:
                effective_status = filters.status
            elif filters.organizer_id is None:
                if filters.status and filters.status != EventStatus.PUBLISHED:
                    effective_organizer_id = current_user.id
                    effective_status = filters.status
                else:
                    effective_status = EventStatus.PUBLISHED
            else:
                effective_status = EventStatus.PUBLISHED

        return await event_repository.list_events(
            db,
            skip=filters.skip,
            limit=filters.limit,
            status=effective_status,
            category=filters.category,
            search=filters.search,
            tag=filters.tag,
            min_price=float(filters.min_price) if filters.min_price is not None else None,
            max_price=float(filters.max_price) if filters.max_price is not None else None,
            sort_by=filters.sort_by,
            date_from=filters.date_from,
            date_to=filters.date_to,
            organizer_id=effective_organizer_id,
        )

    async def list_categories(self, db: AsyncSession) -> list[str]:
        db_categories = await event_repository.list_categories(db)
        defaults = [
            "Arts & Culture",
            "Business",
            "Community",
            "Education",
            "Health",
            "Music",
            "Sports",
            "Technology",
        ]
        return sorted(list(set(db_categories + defaults)))

    async def get_stats(
        self, db: AsyncSession, *, current_user: User
    ) -> EventStatsResponse:
        is_admin = current_user.role == UserRole.ADMIN
        event_filters = [Event.is_deleted.is_(False)]
        if not is_admin:
            event_filters.append(Event.organizer_id == current_user.id)

        total_events = (
            await db.execute(
                select(func.count()).select_from(Event).where(*event_filters)
            )
        ).scalar_one() or 0

        published_events = (
            await db.execute(
                select(func.count())
                .select_from(Event)
                .where(*event_filters, Event.status == EventStatus.PUBLISHED)
            )
        ).scalar_one() or 0

        draft_events = (
            await db.execute(
                select(func.count())
                .select_from(Event)
                .where(*event_filters, Event.status == EventStatus.DRAFT)
            )
        ).scalar_one() or 0

        cancelled_events = (
            await db.execute(
                select(func.count())
                .select_from(Event)
                .where(*event_filters, Event.status == EventStatus.CANCELLED)
            )
        ).scalar_one() or 0

        tickets_sold = (
            await db.execute(
                select(
                    func.coalesce(
                        func.sum(Event.total_tickets - Event.available_tickets), 0
                    )
                ).where(*event_filters)
            )
        ).scalar_one() or 0

        revenue = (
            await db.execute(
                select(
                    func.coalesce(
                        func.sum(
                            Event.ticket_price
                            * (Event.total_tickets - Event.available_tickets)
                        ),
                        0,
                    )
                ).where(*event_filters)
            )
        ).scalar_one() or Decimal("0.00")

        booking_stmt = (
            select(func.count())
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(
                Booking.is_deleted.is_(False),
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        if not is_admin:
            booking_stmt = booking_stmt.where(Event.organizer_id == current_user.id)
        total_bookings = (await db.execute(booking_stmt)).scalar_one() or 0

        total_users = None
        total_organizers = None
        total_attendees = None

        if is_admin:
            total_users = (
                await db.execute(
                    select(func.count())
                    .select_from(User)
                    .where(User.is_deleted.is_(False))
                )
            ).scalar_one() or 0
            total_organizers = (
                await db.execute(
                    select(func.count())
                    .select_from(User)
                    .where(User.is_deleted.is_(False), User.role == UserRole.ORGANIZER)
                )
            ).scalar_one() or 0
            total_attendees = (
                await db.execute(
                    select(func.count())
                    .select_from(User)
                    .where(User.is_deleted.is_(False), User.role == UserRole.ATTENDEE)
                )
            ).scalar_one() or 0

        return EventStatsResponse(
            total_events=total_events,
            published_events=published_events,
            draft_events=draft_events,
            cancelled_events=cancelled_events,
            total_tickets_sold=int(tickets_sold),
            total_revenue=Decimal(str(revenue)),
            total_bookings=total_bookings,
            total_users=total_users,
            total_organizers=total_organizers,
            total_attendees=total_attendees,
        )

    async def update_event(
        self,
        db: AsyncSession,
        *,
        event_id: UUID,
        data: EventUpdateRequest,
        current_user: User,
    ) -> Event:
        event = await self.get_event(db, event_id=event_id, current_user=current_user)
        if (
            current_user.role != UserRole.ADMIN
            and current_user.id != event.organizer_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own events",
            )
        if event.status in [EventStatus.CANCELLED, EventStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit an event with status '{event.status.value}'",
            )
        update_data = data.model_dump(exclude_unset=True)
        if "total_tickets" in update_data:
            diff = update_data["total_tickets"] - event.total_tickets
            if event.available_tickets + diff < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot reduce total tickets below already booked tickets",
                )
            event.available_tickets += diff
        for field, value in update_data.items():
            setattr(event, field, value)

        updated = await event_repository.update(db, event)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def cancel_event(
        self, db: AsyncSession, *, event_id: UUID, current_user: User
    ) -> Event:
        event = await self.get_event(db, event_id=event_id, current_user=current_user)
        if (
            current_user.role != UserRole.ADMIN
            and current_user.id != event.organizer_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own events",
            )
        if event.status == EventStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is already cancelled",
            )
        event.status = EventStatus.CANCELLED
        updated = await event_repository.update(db, event)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def delete_event(
        self, db: AsyncSession, *, event_id: UUID, current_user: User
    ) -> Event:
        event = await event_repository.get_by_id_active(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        if (
            current_user.role != UserRole.ADMIN
            and current_user.id != event.organizer_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own events",
            )
        event.is_deleted = True
        updated = await event_repository.update(db, event)
        await db.commit()
        await db.refresh(updated)
        return updated


event_service = EventService()
