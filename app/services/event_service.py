from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.models.user import User, UserRole
from app.repositories.event_repository import event_repository
from app.schemas.event import EventCreateRequest, EventFilterParams, EventUpdateRequest


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
        return await event_repository.create(db, obj=event)

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
        if not current_user or current_user.role == UserRole.ATTENDEE:
            effective_status = EventStatus.PUBLISHED

        return await event_repository.list_events(
            db,
            skip=filters.skip,
            limit=filters.limit,
            status=effective_status,
            category=filters.category,
            search=filters.search,
            date_from=filters.date_from,
            date_to=filters.date_to,
            organizer_id=filters.organizer_id,
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

        return await event_repository.update(db, event)

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
        return await event_repository.update(db, event)


event_service = EventService()
