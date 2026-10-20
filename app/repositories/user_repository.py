from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole

class UserRepository:
    async def get_by_email(self,db: AsyncSession,email:str)->User | None:
        query= select(User).where(User.email==email, User.is_deleted.is_(False))
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_id(self,db: AsyncSession,user_id:UUID)->User | None:
        query= select(User).where(User.id==user_id, User.is_deleted.is_(False))
        result = await db.execute(query)
        return result.scalars().first()

    async def create(self, db: AsyncSession,email:str, hashed_password:str, role: UserRole) ->User:
        user=User(email=email,hashed_password=hashed_password,role=role,is_active=True,is_deleted=False)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

user_repository=UserRepository() #singleton isntance