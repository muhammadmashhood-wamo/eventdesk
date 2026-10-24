import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from httpx import AsyncClient

from app.core.database import async_session_maker
from app.models.event import Event, EventStatus
from app.models.user import UserRole
from tests.conftest import create_test_user, auth_headers_for


async def create_published_event(total_tickets: int = 10) -> Event:
    organizer = await create_test_user(role=UserRole.ORGANIZER)
    future_date = datetime.now(timezone.utc) + timedelta(days=5)

    async with async_session_maker() as session:
        event = Event(
            title=f"Concert {uuid.uuid4().hex[:6]}",
            description="Live concert event",
            venue="Arena",
            event_date=future_date,
            ticket_price=Decimal("45.00"),
            total_tickets=total_tickets,
            available_tickets=total_tickets,
            status=EventStatus.PUBLISHED,
            organizer_id=organizer.id,
            is_deleted=False,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event


async def test_booking_and_cancellation_flow(client: AsyncClient):
    event = await create_published_event(total_tickets=10)
    attendee = await create_test_user(role=UserRole.ATTENDEE)

    # 1. Book 2 tickets
    book_res = await client.post(
        "/api/v1/bookings",
        json={"event_id": str(event.id), "ticket_count": 2},
        headers=auth_headers_for(attendee),
    )
    assert book_res.status_code == 201
    booking_data = book_res.json()
    assert booking_data["ticket_count"] == 2
    assert booking_data["status"] == "Confirmed"
    booking_id = booking_data["id"]

    # 2. Check remaining tickets on event endpoint
    event_res = await client.get(f"/api/v1/events/{event.id}")
    assert event_res.status_code == 200
    assert event_res.json()["available_tickets"] == 8

    # 3. List my bookings
    my_bookings = await client.get("/api/v1/bookings", headers=auth_headers_for(attendee))
    assert my_bookings.status_code == 200
    assert my_bookings.json()["total"] >= 1

    # 4. Cancel booking
    cancel_res = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=auth_headers_for(attendee),
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Cancelled"

    # 5. Tickets return to pool
    event_res_after = await client.get(f"/api/v1/events/{event.id}")
    assert event_res_after.json()["available_tickets"] == 10


async def test_concurrent_booking_never_oversells(client: AsyncClient):
    """
    CRITICAL CONCURRENCY TEST:
    Event has only 3 tickets.
    10 attendees attempt to book 1 ticket concurrently at the exact same moment.
    System must allow EXACTLY 3 bookings and reject 7. Available tickets must be 0.
    """
    total_tickets = 3
    event = await create_published_event(total_tickets=total_tickets)

    # Create 10 different attendees
    attendees = [
        await create_test_user(role=UserRole.ATTENDEE)
        for _ in range(10)
    ]

    async def book_ticket(user):
        return await client.post(
            "/api/v1/bookings",
            json={"event_id": str(event.id), "ticket_count": 1},
            headers=auth_headers_for(user),
        )

    # Fire all 10 requests at the exact same time
    responses = await asyncio.gather(*[book_ticket(user) for user in attendees])

    success_count = sum(1 for r in responses if r.status_code == 201)
    rejected_count = sum(1 for r in responses if r.status_code == 400)

    # EXACTLY 3 must succeed, 7 must be rejected
    assert success_count == total_tickets, f"Expected {total_tickets} successes, got {success_count}"
    assert rejected_count == len(attendees) - total_tickets

    # Verify event state in DB
    event_res = await client.get(f"/api/v1/events/{event.id}")
    assert event_res.status_code == 200
    assert event_res.json()["available_tickets"] == 0


async def test_concurrent_booking_cancellation_restores_tickets_once(
    client: AsyncClient,
):
    event = await create_published_event(total_tickets=3)
    attendee = await create_test_user(role=UserRole.ATTENDEE)
    headers = auth_headers_for(attendee)

    booking_res = await client.post(
        "/api/v1/bookings",
        json={"event_id": str(event.id), "ticket_count": 2},
        headers=headers,
    )
    assert booking_res.status_code == 201
    booking_id = booking_res.json()["id"]

    async def cancel_booking():
        return await client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=headers,
        )

    responses = await asyncio.gather(cancel_booking(), cancel_booking())

    assert sorted(response.status_code for response in responses) == [200, 400]
    event_res = await client.get(f"/api/v1/events/{event.id}")
    assert event_res.status_code == 200
    assert event_res.json()["available_tickets"] == 3


async def test_all_roles_can_book_published_events(client: AsyncClient):
    event = await create_published_event(total_tickets=3)

    for role in (UserRole.ADMIN, UserRole.ORGANIZER, UserRole.ATTENDEE):
        user = await create_test_user(role=role)
        response = await client.post(
            "/api/v1/bookings",
            json={"event_id": str(event.id), "ticket_count": 1},
            headers=auth_headers_for(user),
        )
        assert response.status_code == 201
        assert response.json()["user_id"] == str(user.id)

    event_res = await client.get(f"/api/v1/events/{event.id}")
    assert event_res.json()["available_tickets"] == 0
