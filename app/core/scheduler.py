import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.core.database import async_session_maker
from app.core.websockets import manager
from app.models.booking import Booking, BookingStatus
from app.models.event import Event, EventStatus
from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def autocomplete_expired_events(self) -> int:
        now = datetime.now(timezone.utc)
        async with async_session_maker() as session:
            stmt = (
                update(Event)
                .where(
                    Event.status == EventStatus.PUBLISHED,
                    Event.event_date <= now,
                    Event.is_deleted.is_(False),
                )
                .values(status=EventStatus.COMPLETED)
            )
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount > 0:
                logger.info(f"Auto-completed {result.rowcount} expired event(s).")

            return result.rowcount

    async def send_upcoming_event_reminders(self) -> int:
        now = datetime.now(timezone.utc)
        in_24h = now + timedelta(hours=24)
        reminders_sent = 0

        async with async_session_maker() as session:
            stmt = (
                select(Event)
                .where(
                    Event.status == EventStatus.PUBLISHED,
                    Event.event_date > now,
                    Event.event_date <= in_24h,
                    Event.is_deleted.is_(False),
                )
            )
            upcoming_events = (await session.execute(stmt)).scalars().all()

            for event in upcoming_events:
                booking_stmt = (
                    select(Booking)
                    .where(
                        Booking.event_id == event.id,
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.is_deleted.is_(False),
                    )
                )
                bookings = (await session.execute(booking_stmt)).scalars().all()

                for booking in bookings:
                    check_stmt = (
                        select(Notification)
                        .where(
                            Notification.user_id == booking.user_id,
                            Notification.type == NotificationType.EVENT_REMINDER,
                            Notification.message.like(f"%'{event.title}'%"),
                        )
                    )
                    existing = (await session.execute(check_stmt)).first()
                    if existing:
                        continue

                    notif = Notification(
                        user_id=booking.user_id,
                        title="Upcoming Event Reminder",
                        message=f"Reminder: '{event.title}' is starting soon on {event.event_date.strftime('%Y-%m-%d %H:%M UTC')}!",
                        type=NotificationType.EVENT_REMINDER,
                        is_read=False,
                    )
                    session.add(notif)
                    await session.commit()
                    await session.refresh(notif)
                    reminders_sent += 1

                    await manager.send_to_user(
                        booking.user_id,
                        {
                            "type": "NEW_NOTIFICATION",
                            "id": str(notif.id),
                            "title": notif.title,
                            "message": notif.message,
                            "notification_type": notif.type.value,
                            "created_at": notif.created_at.isoformat(),
                        },
                    )
        return reminders_sent

    async def _worker_loop(self):
        logger.info("Background scheduler started.")
        while self._running:
            try:
                await self.autocomplete_expired_events()
                await self.send_upcoming_event_reminders()
            except Exception as e:
                logger.error(f"Error in background scheduler: {e}", exc_info=True)

            await asyncio.sleep(60)

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._worker_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()


scheduler = BackgroundScheduler()
