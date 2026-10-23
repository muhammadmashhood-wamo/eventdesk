from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.repositories.notification_repository import notification_repository
from app.core.database import async_session_maker


class NotificationService:
    async def send_notification(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
    ) -> Notification:
        return await notification_repository.create_notification(
            db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )

    @staticmethod
    async def send_background_notification(
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
    ) -> None:
        async with async_session_maker() as session:
            await notification_repository.create_notification(
                session,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
            )

    async def list_notifications(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        is_read: bool | None = None,
        notification_type: NotificationType | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int, int]:
        items, total = await notification_repository.list_user_notifications(
            db,
            user_id=current_user.id,
            is_read=is_read,
            notification_type=notification_type,
            skip=skip,
            limit=limit,
        )
        unread_count = await notification_repository.get_unread_count(
            db, user_id=current_user.id
        )
        return items, total, unread_count

    async def set_read_status(
        self,
        db: AsyncSession,
        *,
        notification_id: UUID,
        current_user: User,
        is_read: bool,
    ) -> Notification:
        notification = await notification_repository.update_read_status(
            db,
            notification_id=notification_id,
            user_id=current_user.id,
            is_read=is_read,
        )
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        return notification

    async def mark_all_notifications_as_read(
        self, db: AsyncSession, *, current_user: User
    ) -> int:
        return await notification_repository.mark_all_as_read(
            db, user_id=current_user.id
        )

    @staticmethod
    async def notify_event_cancelled(event_id: UUID, event_title: str) -> None:
        from sqlalchemy import select
        from app.models.booking import Booking, BookingStatus

        async with async_session_maker() as session:
            stmt = (
                select(Booking.user_id)
                .where(
                    Booking.event_id == event_id,
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.is_deleted.is_(False),
                )
                .distinct()
            )
            user_ids = (await session.execute(stmt)).scalars().all()
            for uid in user_ids:
                await notification_repository.create_notification(
                    session,
                    user_id=uid,
                    title="Event Cancelled",
                    message=f"The event '{event_title}' has been cancelled.",
                    notification_type=NotificationType.EVENT_CANCELLED,
                )


notification_service = NotificationService()

