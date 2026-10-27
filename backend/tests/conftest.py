import os
os.environ["TESTING"] = "1"

import asyncio
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import hash_password, create_access_token
from app.main import app
from app.models.user import User, UserRole


@pytest_asyncio.fixture(scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def create_test_user(
    role: UserRole = UserRole.ATTENDEE,
    email: str | None = None,
    password: str = "StrongPass123!",
) -> User:
    if not email:
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    async with async_session_maker() as session:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def auth_headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}
