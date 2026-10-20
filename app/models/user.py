from sqlalchemy.orm import Relationship
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.event import Event
    from app.models.review import Review

class UserRole(str,enum.Enum):
    ADMIN="Admin"
    ORGANIZER="Organizer"
    ATTENDEE = "Attendee"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column( UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(256),unique=True,index=True,nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256),nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole),default = UserRole.ATTENDEE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean,default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),onupdate=datetime.now(timezone.utc))
    events: Mapped[list["Event"]] = Relationship(
        "Event",back_populates="organizer"
    )
    bookings: Mapped[list["Booking"]] = Relationship(
        "Booking",back_populates="user"
    )
    reviews: Mapped[list["Review"]] = Relationship(
        "Review",back_populates= "user"
    )
    