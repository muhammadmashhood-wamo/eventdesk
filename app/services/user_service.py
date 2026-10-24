from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import user_repository
from app.schemas.user import (
    UserAdminUpdateRequest,
    UserPasswordChangeRequest,
    UserProfileUpdateRequest,
)

class UserService:
    async def update_profile(
        self,db: AsyncSession, *, current_user: User, data: UserProfileUpdateRequest
    ):
        if data.name is not None:
            current_user.name = data.name
        if data.email and data.email != current_user.email:
            existing = await user_repository.get_by_email(db,email=data.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists.",
                )
            current_user.email = data.email
        return await user_repository.update(db,current_user)
    
    async def change_password(self,db:AsyncSession,*,current_user: User, data: UserPasswordChangeRequest)->None:
        if not verify_password(data.current_password,current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password.",
            )
        
        if verify_password(data.new_password,current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as the current password.",
            )
        current_user.hashed_password = hash_password(data.new_password)
        await user_repository.update(db,current_user)

    async def list_users(self, db:AsyncSession, *, skip:int = 0, limit:int = 20)-> tuple[list[User],int]:
        return await user_repository.list_users(db,skip=skip,limit=limit)

    async def admin_update_user(
        self,
        db:AsyncSession,
        *,
        target_user_id: UUID,
        current_admin: User,
        data: UserAdminUpdateRequest
    ) -> User:
        target_user = await user_repository.get_by_id(db,target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if target_user.id == current_admin.id:
            if data.is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admins cannot deactivate their own account.",
                )
            if data.role and data.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admins cannot demote their own role.",
                )
        if data.role is not None:
            target_user.role = data.role
        if data.is_active is not None:
            target_user.is_active = data.is_active
            
        return await user_repository.update(db,target_user)

user_service = UserService()