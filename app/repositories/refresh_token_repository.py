from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def create_token(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        token_hash: str,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
        )
        db.add(token)
        await db.flush()
        return token

    async def get_by_jti(self, db: AsyncSession, *, jti: str) -> RefreshToken | None:
        query = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_token_hash(
        self, db: AsyncSession, *, token_hash: str
    ) -> RefreshToken | None:
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(query)
        return result.scalars().first()

    async def revoke(
        self, db: AsyncSession, *, refresh_token: RefreshToken
    ) -> RefreshToken:
        refresh_token.revoked_at = datetime.now(UTC)
        await db.flush()
        return refresh_token

    async def revoke_all_for_user(self, db: AsyncSession, *, user_id: UUID) -> int:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount


refresh_token_repository = RefreshTokenRepository()
