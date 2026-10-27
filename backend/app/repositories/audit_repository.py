from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.repositories.base import BaseRepository

class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def log_action(
        self, db: AsyncSession, *, user_id: UUID | None, action: str, details: str | None = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
        )
        return await self.create(db, log_entry)

    async def list_audit_logs(
        self,
        db: AsyncSession,
        *,
        action: str | None = None,
        user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[AuditLog], int]:
        filters=[]
        if action:
            filters.append(AuditLog.action==action)
        if user_id:
            filters.append(AuditLog.user_id==user_id)
        count_stmt = select(func.count()).select_from(AuditLog)
        if filters:
            count_stmt=count_stmt.where(*filters)

        total = ( await db.execute(count_stmt)).scalar_one()

        row_stmt = select(AuditLog)
        if filters:
            row_stmt = row_stmt.where(*filters)
        row_stmt = row_stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        rows = list((await db.execute(row_stmt)).scalars().all())
        return rows, total
    
audit_repository = AuditRepository()