from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str
    details: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int
