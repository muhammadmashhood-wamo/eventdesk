import uuid
import pytest
from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "StrongPassword123!",
        "role": "Attendee",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "Attendee"
    assert "password" not in data


async def test_register_weak_password_rejected(client: AsyncClient):
    # Too short
    res_short = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "weak"},
    )
    assert res_short.status_code == 422

    # Missing uppercase / special char
    res_no_special = await client.post(
        "/api/v1/auth/register",
        json={"email": "nospecial@example.com", "password": "password123"},
    )
    assert res_no_special.status_code == 422


async def test_register_admin_prevented(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"hacker_{uuid.uuid4().hex[:8]}@example.com",
            "password": "StrongPassword123!",
            "role": "Admin",
        },
    )
    assert response.status_code == 422


async def test_login_success_and_refresh(client: AsyncClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    # 1. Register
    reg_res = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert reg_res.status_code == 201

    # 2. Login
    login_res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # 3. Refresh Token
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


async def test_login_invalid_password(client: AsyncClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword123!"},
    )

    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "WrongPassword123!"}
    )
    assert response.status_code == 401
