from uuid import UUID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    async def create_notification(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            is_read=False,
        )
        return await self.create(db, notification)

    async def list_user_notifications(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        is_read: bool | None = None,
        notification_type: NotificationType | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        filters = [Notification.user_id == user_id]
        if is_read is not None:
            filters.append(Notification.is_read.is_(is_read))
        if notification_type is not None:
            filters.append(Notification.type == notification_type)

        total_stmt = select(func.count()).select_from(Notification).where(*filters)
        total = (await db.execute(total_stmt)).scalar_one()

        row_stmt = (
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await db.execute(row_stmt)).scalars().all())
        return rows, total

    async def get_unread_count(self, db: AsyncSession, *, user_id: UUID) -> int:
        count_stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return (await db.execute(count_stmt)).scalar_one()

    async def update_read_status(
        self, db: AsyncSession, *, notification_id: UUID, user_id: UUID, is_read: bool
    ) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        notification = (await db.execute(stmt)).scalar_one_or_none()
        if not notification:
            return None

        notification.is_read = is_read
        return await self.update(db, notification)

    async def mark_all_as_read(self, db: AsyncSession, *, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount


notification_repository = NotificationRepository()

