from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.event import EventStatus


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=2048)
    category: str | None = Field(default=None, max_length=120)
    venue: str = Field(..., min_length=1, max_length=256)
    event_date: datetime
    ticket_price: Decimal = Field(..., gt=0)
    total_tickets: int = Field(..., gt=0)
    tags: list[str] | None = Field(default_factory=list)


class EventCreateRequest(EventBase):
    status: EventStatus = EventStatus.DRAFT

    @field_validator("event_date")
    @classmethod
    def validate_future_date(cls, value: datetime) -> datetime:
        current_time = datetime.now(UTC)
        if value.tzinfo is None:
            target_time = value.replace(tzinfo=UTC)
        else:
            target_time = value.astimezone(UTC)

        if target_time <= current_time:
            raise ValueError("Event date must be in future.")

        return target_time


class EventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=2048)
    category: str | None = Field(default=None, max_length=120)
    venue: str | None = Field(default=None, min_length=1, max_length=256)
    event_date: datetime | None = None
    ticket_price: Decimal | None = Field(default=None, ge=0)
    total_tickets: int | None = Field(default=None, gt=0)
    tags: list[str] | None = None
    status: EventStatus | None = None

    @field_validator("event_date")
    @classmethod
    def validate_future_date(cls, value: datetime) -> datetime:
        current_time = datetime.now(UTC)
        if value.tzinfo is None:
            target_time = value.replace(tzinfo=UTC)
        else:
            target_time = value.astimezone(UTC)

        if target_time <= current_time:
            raise ValueError("Event date must be in future.")

        return target_time


class EventStatusUpdate(BaseModel):
    status: EventStatus


class EventResponse(BaseModel):
    id: UUID
    organizer_id: UUID
    title: str
    description: str
    venue: str
    event_date: datetime
    ticket_price: Decimal
    total_tickets: int
    available_tickets: int
    status: EventStatus
    category: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    skip: int
    limit: int


class EventFilterParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    status: EventStatus | None = None
    category: str | None = None
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    organizer_id: UUID | None = None
