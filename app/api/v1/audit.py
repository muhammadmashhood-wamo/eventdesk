from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="View activity and audit logs (Admin only)",
)
async def list_audit_logs(
    action: str | None = Query(None, description="Filter by action name"),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    items, total = await audit_service.list_logs(
        db, action=action, user_id=user_id, skip=skip, limit=limit
    )
    return AuditLogListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )
