from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.booking import BookingStatus
from app.schemas.event import EventResponse


class BookingCreateRequest(BaseModel):
    event_id: UUID
    ticket_count: int = Field(default=1, ge=1, le=10, description="Number of tickets to book (1 to 10)")


class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    ticket_count: int
    status: BookingStatus
    created_at: datetime
    event: EventResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    skip: int
    limit: int
