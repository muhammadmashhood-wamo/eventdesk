# Endpoint coverage map

This file maps each backend route or websocket to the page or component that consumes it in the frontend.

| Endpoint | Method | Used by | Notes |
| --- | --- | --- | --- |
| `/api/v1/auth/register` | POST | Register page | User self-registration for attendee/organizer roles |
| `/api/v1/auth/login` | POST | Login page | Login and session initialization |
| `/api/v1/auth/refresh` | POST | API client refresh flow | Replaces expired access token and refresh token |
| `/api/v1/auth/logout` | POST | Navbar / AuthContext | Stateless logout and local state cleanup |
| `/api/v1/auth/me` | GET | AuthContext | Restores session on page reload |
| `/api/v1/events` | GET | Events page, My Events page | Public listing with page/filters |
| `/api/v1/events` | POST | EventFormPage | Organizer/admin event creation |
| `/api/v1/events/{event_id}` | GET | Event detail page | Event read and permissions check |
| `/api/v1/events/{event_id}` | PATCH | EventFormPage | Edit or publish a draft event |
| `/api/v1/events/{event_id}/cancel` | POST | Event detail page, My Events page | Cancel event with confirmation |
| `/api/v1/events/categories` | GET | Events page | Category suggestions for datalist |
| `/api/v1/events/dashboard` | GET | My Events page | Organizer dashboard stats |
| `/api/v1/bookings` | POST | Event detail page | Ticket booking action |
| `/api/v1/bookings` | GET | Bookings page | Currrent-user bookings list |
| `/api/v1/bookings/{booking_id}/cancel` | POST | Bookings page | Cancel booking |
| `/api/v1/users/me` | PATCH | Profile page | Update email |
| `/api/v1/users/me/change-password` | POST | Profile page | Change password |
| `/api/v1/users` | GET | Admin users table | List users for admin management |
| `/api/v1/users/{user_id}` | PATCH | Admin users table | Change role or active state |
| `/api/v1/reviews/events/{event_id}` | GET | Event detail page | Event reviews list |
| `/api/v1/reviews/events/{event_id}` | POST | Event detail page | Top-level review or reply |
| `/api/v1/reviews/{review_id}` | PATCH | Event detail page | Edit user review |
| `/api/v1/reviews/{review_id}` | DELETE | Event detail page | Delete user review |
| `/api/v1/notifications` | GET | Notifications page, Navbar | Unread count and list |
| `/api/v1/notifications/{id}/read` | PATCH | Notifications page | Mark single notification as read |
| `/api/v1/notifications/{id}/unread` | PATCH | Notifications page | Mark single notification as unread |
| `/api/v1/notifications/read-all` | POST | Notifications page | Mark all seen |
| `/api/v1/audit-logs` | GET | Admin audit logs page | Admin log query and filters |
| `/api/v1/ws/events/{event_id}` | WebSocket | Event detail page | Live ticket availability updates |
| `/api/v1/ws/notifications` | WebSocket | Navbar / notifications hook | Live notification push |
| `/health` | GET | App boot check | Optional health validation |

## Notes

- The routes are consumed through the central API wrapper in `src/api.js` and the websocket hooks in `src/hooks`.
- Unsupported backend features are intentionally not implemented in the UI; they are described in `BACKEND_GAPS.md`.
