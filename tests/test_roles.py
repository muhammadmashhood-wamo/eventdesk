import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from tests.conftest import create_test_user, auth_headers_for


async def test_role_event_creation_permissions(client: AsyncClient):
    attendee = await create_test_user(role=UserRole.ATTENDEE)
    organizer = await create_test_user(role=UserRole.ORGANIZER)

    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    event_payload = {
        "title": "Music Fest",
        "description": "Fun weekend fest",
        "venue": "Convention Center",
        "event_date": future_date,
        "total_tickets": 100,
        "ticket_price": 50.0,
        "category": "Music",
    }

    # 1. Attendee tries to create event -> 403 Forbidden
    res_attendee = await client.post(
        "/api/v1/events",
        json=event_payload,
        headers=auth_headers_for(attendee),
    )
    assert res_attendee.status_code == 403

    # 2. Organizer creates event -> 201 Created
    res_organizer = await client.post(
        "/api/v1/events",
        json=event_payload,
        headers=auth_headers_for(organizer),
    )
    assert res_organizer.status_code == 201
    assert res_organizer.json()["title"] == "Music Fest"


async def test_role_admin_user_management(client: AsyncClient):
    admin = await create_test_user(role=UserRole.ADMIN)
    attendee = await create_test_user(role=UserRole.ATTENDEE)
    organizer = await create_test_user(role=UserRole.ORGANIZER)

    # 1. Attendee cannot view all users
    res_att = await client.get("/api/v1/users", headers=auth_headers_for(attendee))
    assert res_att.status_code == 403

    # 2. Admin can view all users
    res_admin = await client.get("/api/v1/users", headers=auth_headers_for(admin))
    assert res_admin.status_code == 200
    assert "items" in res_admin.json()

    # 3. Organizer cannot change user role
    res_org_change = await client.patch(
        f"/api/v1/users/{attendee.id}",
        json={"role": "Organizer"},
        headers=auth_headers_for(organizer),
    )
    assert res_org_change.status_code == 403

    # 4. Admin can change user role
    res_admin_change = await client.patch(
        f"/api/v1/users/{attendee.id}",
        json={"role": "Organizer"},
        headers=auth_headers_for(admin),
    )
    assert res_admin_change.status_code == 200
    assert res_admin_change.json()["role"] == "Organizer"
