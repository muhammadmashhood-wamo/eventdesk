# Backend Gaps and Verified API Behavior

This document reflects the running API contract and the local QA flows exercised against it. Backend source files were not modified.

## Verified API behavior

- Event listing supports search, category, status, date range, tag, min/max price, sort order, organizer ID, and pagination. Matching controls are available in the Events UI; status is restricted to organizer/admin views.
- Categories and organizer/admin event statistics are available through `/events/categories`, `/events/stats`, and `/events/dashboard`.
- Organizers can fetch and list their own drafts. Public draft detail requests are denied; published events remain publicly discoverable.
- Booking creation uses a row-level `SELECT FOR UPDATE` lock before decrementing inventory. Concurrent QA requests for three tickets produced exactly three confirmed bookings, seven sold-out rejections, and zero remaining tickets.
- Reviews require a confirmed booking for attendees. Organizers cannot review their own events; only the event organizer or an admin can reply. Admins can moderate reviews, and review lists include author metadata, nested replies, and a total count.
- Event deletion is implemented as a soft delete. Cancellation notifies attendees and writes audit records.
- User profile email/password changes, admin user role/status changes, audit-log filtering, notifications, and real-time event-ticket/notification WebSockets are implemented and exercised.
- The scheduler auto-completes expired events and persists upcoming-event reminders. Reminder creation is idempotent in repeated scheduler runs.

## Remaining backend gaps

### Notification target identifiers

- `NEW_NOTIFICATION` payloads contain notification metadata but no event or entity ID.
- Suggested fix: include `event_id` and `entity_id` where the notification relates to a specific resource, enabling precise frontend links.

### Scheduler administration

- The scheduler runs inside the application, but there are no endpoints for health/status, configuration, or manual dispatch.
- Suggested fix: expose admin-only scheduler status and task-health endpoints; keep task execution and idempotency on the server.

### Attendee export

- There is no organizer-facing event attendee-list/export endpoint.
- Suggested fix: add an organizer-owned `/events/{event_id}/attendees` endpoint with pagination and explicit privacy rules.

### Unimplemented product services

- Password reset, MFA, payment processing, and recurring event scheduling are not exposed by the API.
- Suggested fix: define their authentication/payment contracts before adding UI controls; the frontend should not simulate successful operations.
