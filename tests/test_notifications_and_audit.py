import uuid
from httpx import AsyncClient

from app.core.database import async_session_maker
from app.models.notification import Notification, NotificationType
from app.models.user import UserRole
from tests.conftest import create_test_user, auth_headers_for


async def test_notifications_crud_and_filtering(client: AsyncClient):
    user = await create_test_user(role=UserRole.ATTENDEE)

    # 1. Manually insert notifications
    async with async_session_maker() as session:
        notif1 = Notification(
            user_id=user.id,
            title="Booking 1",
            message="Your booking 1 is confirmed",
            type=NotificationType.BOOKING,
            is_read=False,
        )
        notif2 = Notification(
            user_id=user.id,
            title="Review Reply",
            message="Someone replied to your review",
            type=NotificationType.REVIEW,
            is_read=False,
        )
        session.add_all([notif1, notif2])
        await session.commit()
        await session.refresh(notif1)
        await session.refresh(notif2)
        notif1_id = notif1.id

    # 2. List notifications -> 2 items, 2 unread
    res = await client.get("/api/v1/notifications", headers=auth_headers_for(user))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["unread_count"] == 2

    # 3. Mark notif1 as read
    patch_res = await client.patch(
        f"/api/v1/notifications/{notif1_id}/read",
        headers=auth_headers_for(user),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_read"] is True

    # 4. Filter by unread
    unread_res = await client.get(
        "/api/v1/notifications?is_read=false",
        headers=auth_headers_for(user),
    )
    assert unread_res.status_code == 200
    assert unread_res.json()["total"] == 1

    # 5. Mark all as read
    all_res = await client.post(
        "/api/v1/notifications/read-all",
        headers=auth_headers_for(user),
    )
    assert all_res.status_code == 200

    # 6. Check unread count is now 0
    final_res = await client.get("/api/v1/notifications", headers=auth_headers_for(user))
    assert final_res.json()["unread_count"] == 0


async def test_audit_logs_admin_access(client: AsyncClient):
    admin = await create_test_user(role=UserRole.ADMIN)
    attendee = await create_test_user(role=UserRole.ATTENDEE)

    # 1. Non-admin cannot view audit logs
    res_att = await client.get("/api/v1/audit-logs", headers=auth_headers_for(attendee))
    assert res_att.status_code == 403

    # 2. Admin can view audit logs
    res_admin = await client.get("/api/v1/audit-logs", headers=auth_headers_for(admin))
    assert res_admin.status_code == 200
    assert "items" in res_admin.json()
    assert "total" in res_admin.json()
