from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserAdminUpdateRequest,
    UserListResponse,
    UserPasswordChangeRequest,
    UserProfileUpdateRequest,
    UserResponse,
)
from app.services.audit_service import audit_service
from app.services.user_service import user_service
router = APIRouter(prefix="/users", tags=["Users"])

@router.patch("/me",response_model=UserResponse,summary="Update own profile")
async def update_my_profile(
    payload: UserProfileUpdateRequest,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await user_service.update_profile(db,current_user=current_user,data=payload)

@router.post("/me/change-password",status_code=status.HTTP_200_OK,summary="Change own password")
async def change_my_password(
    payload: UserPasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await user_service.change_password(db, current_user = current_user, data = payload)
    return { "detail": "Password changed successfully"}

@router.get(
    "",response_model=UserListResponse,
    summary="List all users (Admin only)",
)
async def list_all_users(
    skip: int = Query(default=0,ge=0),
    limit: int = Query(default=20,ge=1,le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    items,total = await user_service.list_users(db,skip=skip,limit=limit)
    return UserListResponse(items = items, total = total, skip = skip, limit = limit)

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="update another user's role or status - only admin allowed to do it"
)
async def admin_update_user(
    user_id: UUID,
    payload: UserAdminUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user:User = Depends(require_role([UserRole.ADMIN])),
):
    updated_user = await user_service.admin_update_user(db,target_user_id=user_id,current_admin=current_user,data = payload)
    details = []
    if payload.role is not None:
        details.append(f"role to {payload.role.value}")
    if payload.is_active is not None:
        details.append(f"is_active to {payload.is_active}")
    details_str = ", ".join(details) if details else "profile"
    background_tasks.add_task(
        audit_service.log_background,
        user_id=current_user.id,
        action="USER_UPDATED_BY_ADMIN",
        details=f"Admin updated user {user_id}: changed {details_str}",
    )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    deleted_user = await user_service.admin_delete_user(
        db,
        target_user_id=user_id,
        current_admin=current_user,
    )
    background_tasks.add_task(
        audit_service.log_background,
        user_id=current_user.id,
        action="USER_DELETED_BY_ADMIN",
        details=f"Admin soft-deleted user {deleted_user.id}",
    )
    