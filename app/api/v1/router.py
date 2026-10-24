from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.events import router as events_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.users import router as users_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.websockets import router as ws_router
from app.api.v1.audit import router as audit_router

api_router = APIRouter()

api_router.include_router(auth_router)

api_router.include_router(events_router)

api_router.include_router(bookings_router)

api_router.include_router(users_router)

api_router.include_router(reviews_router)

api_router.include_router(notifications_router)

api_router.include_router(ws_router)

api_router.include_router(audit_router)

