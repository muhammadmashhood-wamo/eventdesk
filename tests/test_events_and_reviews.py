import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.models.event import EventStatus
from app.models.user import UserRole
from tests.conftest import create_test_user, auth_headers_for


async def test_event_categories_and_stats(client: AsyncClient):
    organizer = await create_test_user(role=UserRole.ORGANIZER)
    admin = await create_test_user(role=UserRole.ADMIN)

    # 1. Categories endpoint works
    cat_res = await client.get("/api/v1/events/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json()
    assert isinstance(categories, list)
    assert "Technology" in categories

    # 2. Organizer stats
    stats_res = await client.get("/api/v1/events/stats", headers=auth_headers_for(organizer))
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_events" in stats
    assert "published_events" in stats
    assert "total_tickets_sold" in stats
    assert "total_revenue" in stats

    # 3. Admin stats includes user breakdown
    admin_stats_res = await client.get("/api/v1/events/dashboard", headers=auth_headers_for(admin))
    assert admin_stats_res.status_code == 200
    admin_stats = admin_stats_res.json()
    assert admin_stats["total_users"] is not None


async def test_event_delete_and_advanced_filters(client: AsyncClient):
    organizer = await create_test_user(role=UserRole.ORGANIZER)
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    # Create event
    create_res = await client.post(
        "/api/v1/events",
        json={
            "title": "AI Summit 2026",
            "description": "Premier tech summit",
            "venue": "Hall A",
            "event_date": future_date,
            "total_tickets": 50,
            "ticket_price": 75.0,
            "category": "Technology",
            "tags": ["ai", "tech"],
            "status": "Published",
        },
        headers=auth_headers_for(organizer),
    )
    assert create_res.status_code == 201
    event_id = create_res.json()["id"]

    # Filter by tag
    tag_res = await client.get("/api/v1/events?tag=ai")
    assert tag_res.status_code == 200
    assert any(e["id"] == event_id for e in tag_res.json()["items"])

    # Filter by price range
    price_res = await client.get("/api/v1/events?min_price=50&max_price=100")
    assert price_res.status_code == 200
    assert any(e["id"] == event_id for e in price_res.json()["items"])

    # Sorting
    sort_res = await client.get("/api/v1/events?sort_by=price_desc")
    assert sort_res.status_code == 200

    # Delete event
    del_res = await client.delete(
        f"/api/v1/events/{event_id}",
        headers=auth_headers_for(organizer),
    )
    assert del_res.status_code == 204

    # Verify event is deleted
    get_res = await client.get(f"/api/v1/events/{event_id}")
    assert get_res.status_code == 404


async def test_review_flow_booking_requirement_and_replies(client: AsyncClient):
    organizer = await create_test_user(role=UserRole.ORGANIZER)
    attendee = await create_test_user(role=UserRole.ATTENDEE)
    unbooked_attendee = await create_test_user(role=UserRole.ATTENDEE)
    admin = await create_test_user(role=UserRole.ADMIN)

    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()

    # Create published event
    create_res = await client.post(
        "/api/v1/events",
        json={
            "title": "Concert 2026",
            "description": "Live musical concert",
            "venue": "Grand Arena",
            "event_date": future_date,
            "total_tickets": 20,
            "ticket_price": 30.0,
            "status": "Published",
        },
        headers=auth_headers_for(organizer),
    )
    assert create_res.status_code == 201
    event_id = create_res.json()["id"]

    # 1. Unbooked attendee tries to review -> 403 Forbidden
    res_unbooked = await client.post(
        f"/api/v1/reviews/events/{event_id}",
        json={"rating": 5, "comment": "Loved the sound!"},
        headers=auth_headers_for(unbooked_attendee),
    )
    assert res_unbooked.status_code == 403

    # 2. Organizer tries to review their own event -> 400 Bad Request
    res_self_review = await client.post(
        f"/api/v1/reviews/events/{event_id}",
        json={"rating": 5, "comment": "My own great event!"},
        headers=auth_headers_for(organizer),
    )
    assert res_self_review.status_code == 400

    # 3. Attendee books tickets
    booking_res = await client.post(
        "/api/v1/bookings",
        json={"event_id": event_id, "ticket_count": 2},
        headers=auth_headers_for(attendee),
    )
    assert booking_res.status_code == 201

    # 4. Now booked attendee leaves a review -> 201 Created
    review_res = await client.post(
        f"/api/v1/reviews/events/{event_id}",
        json={"rating": 5, "comment": "Amazing concert experience!"},
        headers=auth_headers_for(attendee),
    )
    assert review_res.status_code == 201
    review_data = review_res.json()
    assert review_data["rating"] == 5
    assert review_data["user_email"] == attendee.email
    assert review_data["user_name"] is not None
    review_id = review_data["id"]

    # 5. Non-organizer attendee tries to reply -> 403 Forbidden
    res_attendee_reply = await client.post(
        f"/api/v1/reviews/events/{event_id}",
        json={"comment": "I am a stranger replying", "parent_review_id": review_id},
        headers=auth_headers_for(unbooked_attendee),
    )
    assert res_attendee_reply.status_code == 403

    # 6. Event organizer replies -> 201 Created
    res_org_reply = await client.post(
        f"/api/v1/reviews/events/{event_id}",
        json={"comment": "Thank you for joining us!", "parent_review_id": review_id},
        headers=auth_headers_for(organizer),
    )
    assert res_org_reply.status_code == 201
    reply_data = res_org_reply.json()
    assert reply_data["user_email"] == organizer.email

    # 7. List reviews returns total count and nested replies
    list_res = await client.get(f"/api/v1/reviews/events/{event_id}")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "total" in list_data
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1
    assert len(list_data["items"][0]["replies"]) == 1

    # 8. Admin can edit review
    admin_edit = await client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"comment": "Moderated review comment"},
        headers=auth_headers_for(admin),
    )
    assert admin_edit.status_code == 200
    assert admin_edit.json()["comment"] == "Moderated review comment"

    # 9. Admin can delete review
    admin_del = await client.delete(
        f"/api/v1/reviews/{review_id}",
        headers=auth_headers_for(admin),
    )
    assert admin_del.status_code == 204


async def test_review_mentions_notify_matching_users_once(client: AsyncClient):
    organizer = await create_test_user(role=UserRole.ORGANIZER)
    reviewer = await create_test_user(role=UserRole.ATTENDEE)
    mentioned = await create_test_user(role=UserRole.ATTENDEE)
    event_date = (datetime.now(timezone.utc) + timedelta(days=8)).isoformat()
    event_res = await client.post(
        "/api/v1/events",
        json={
            "title": "Mention Notification Event",
            "description": "Event for review mention notifications",
            "venue": "Review Hall",
            "event_date": event_date,
            "total_tickets": 5,
            "ticket_price": 12,
            "status": "Published",
        },
        headers=auth_headers_for(organizer),
    )
    assert event_res.status_code == 201
    event_id = event_res.json()["id"]

    booking_res = await client.post(
        "/api/v1/bookings",
        json={"event_id": event_id, "ticket_count": 1},
        headers=auth_headers_for(reviewer),
    )
    assert booking_res.status_code == 201

    review_res = await client.post(
        f"/api/v1/reviews/events/{event_id}",
        json={
            "rating": 5,
            "comment": f"Thanks @{mentioned.email} and @{mentioned.email}; @{reviewer.email}",
        },
        headers=auth_headers_for(reviewer),
    )
    assert review_res.status_code == 201

    mentioned_notifications = await client.get(
        "/api/v1/notifications?type=Review",
        headers=auth_headers_for(mentioned),
    )
    assert mentioned_notifications.status_code == 200
    mentions = [
        item
        for item in mentioned_notifications.json()["items"]
        if item["title"] == "You were mentioned in a review"
    ]
    assert len(mentions) == 1

    reviewer_notifications = await client.get(
        "/api/v1/notifications?type=Review",
        headers=auth_headers_for(reviewer),
    )
    assert reviewer_notifications.status_code == 200
    assert not any(
        item["title"] == "You were mentioned in a review"
        for item in reviewer_notifications.json()["items"]
    )
