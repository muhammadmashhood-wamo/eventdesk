from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.models.audit import AuditLog
from app.repositories.audit_repository import audit_repository


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        *,
        user_id: UUID | None,
        action: str,
        details: str | None = None,
    ) -> AuditLog:
        return await audit_repository.log_action(
            db, user_id=user_id, action=action, details=details
        )
    
    @staticmethod
    async def log_background(
        user_id: UUID | None,
        action: str,
        details: str | None = None,
    ) -> None:
        async with async_session_maker() as session:
            await audit_repository.log_action(
                session, user_id=user_id, action=action, details=details
            )
    
    async def list_logs(
        self,
        db: AsyncSession,
        *,
        action: str | None = None,
        user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[AuditLog], int]:
        return await audit_repository.list_audit_logs(
            db, action=action, user_id=user_id, skip=skip, limit=limit
        )
        
audit_service = AuditService()
