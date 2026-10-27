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
    res_short = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "weak"},
    )
    assert res_short.status_code == 422

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

    reg_res = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

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


async def test_user_can_register_and_update_display_name(client: AsyncClient):
    email = f"named_{uuid.uuid4().hex[:8]}@example.com"
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "name": "Event Attendee",
        },
    )
    assert registration.status_code == 201
    assert registration.json()["name"] == "Event Attendee"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = login.json()["access_token"]
    updated = await client.patch(
        "/api/v1/users/me",
        json={"name": "Event Host"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Event Host"


async def test_refresh_token_rotation_invalidates_previous_token(client: AsyncClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    login_res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    initial_tokens = login_res.json()

    first_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial_tokens["refresh_token"]},
    )
    assert first_refresh.status_code == 200

    second_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial_tokens["refresh_token"]},
    )
    assert second_refresh.status_code == 401


async def test_refresh_token_reuse_detection_revokes_family(client: AsyncClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    login_res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    initial_tokens = login_res.json()

    first_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial_tokens["refresh_token"]},
    )
    assert first_refresh.status_code == 200
    rotated_tokens = first_refresh.json()

    stolen_replay = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial_tokens["refresh_token"]},
    )
    assert stolen_replay.status_code == 401

    legitimate_attempt = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_tokens["refresh_token"]},
    )
    assert legitimate_attempt.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    login_res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    tokens = login_res.json()

    logout_res = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_res.status_code == 200

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 401

