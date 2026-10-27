import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class BookingStatus(str, enum.Enum):
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False
    )
    ticket_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    user: Mapped["User"] = relationship("User", back_populates="bookings")
    event: Mapped["Event"] = relationship("Event", back_populates="bookings")

    @property
    def user_email(self) -> str | None:
        user = self.__dict__.get("user")
        return user.email if user is not None else None

    @property
    def user_name(self) -> str | None:
        user = self.__dict__.get("user")
        if user is not None:
            return user.name or user.email.split("@")[0]
        return None

