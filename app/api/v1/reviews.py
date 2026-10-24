from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.notification import NotificationType
from app.models.review import Review
from app.models.user import User, UserRole
from app.repositories.event_repository import event_repository
from app.repositories.review_repository import review_repository
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewListResponse,
    ReviewReplyResponse,
    ReviewResponse,
    ReviewUpdateRequest,
)
from app.services.notification_service import notification_service
from app.services.review_service import review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _build_nested(reviews: list[Review]) -> list[ReviewResponse]:
    """
    Given a flat list of top-level reviews (already filtered by the repository),
    attach their non-deleted replies and return nested ReviewResponse objects.
    """
    result: list[ReviewResponse] = []
    for parent in reviews:
        parent_resp = ReviewResponse.model_validate(parent)
        parent_resp.replies = [
            ReviewReplyResponse.model_validate(r)
            for r in parent.replies
            if not r.is_deleted
        ]
        result.append(parent_resp)
    return result


@router.post(
    "/events/{event_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review or a reply to a review for an event",
)
async def create_review(
    event_id: UUID,
    payload: ReviewCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = await review_service.create_review(
        db,
        event_id=event_id,
        user_id=current_user.id,
        user_role=current_user.role,
        data=payload,
    )
    fresh = await review_repository.get_by_id(db, review.id)

    if payload.parent_review_id:
        parent = await review_repository.get_by_id(db, payload.parent_review_id)
        if parent and parent.user_id != current_user.id:
            background_tasks.add_task(
                notification_service.send_background_notification,
                user_id=parent.user_id,
                title="New Reply to Your Review",
                message=f"{current_user.email} replied to your review.",
                notification_type=NotificationType.REVIEW,
            )
    else:
        event = await event_repository.get_by_id_active(db, event_id)
        if event and event.organizer_id != current_user.id:
            background_tasks.add_task(
                notification_service.send_background_notification,
                user_id=event.organizer_id,
                title="New Review on Your Event",
                message=f"{current_user.email} left a review on '{event.title}'.",
                notification_type=NotificationType.REVIEW,
            )

    return ReviewResponse.model_validate(fresh)


@router.get(
    "/events/{event_id}",
    response_model=ReviewListResponse,
    summary="List reviews for an event (top-level with replies nested)",
)
async def list_reviews(
    event_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    reviews, total = await review_service.list_by_event(
        db, event_id=event_id, skip=skip, limit=limit
    )
    return ReviewListResponse(
        items=_build_nested(reviews),
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Update your own review or reply",
)
async def update_review(
    review_id: UUID,
    payload: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review: Review | None = await review_repository.get_by_id(db, review_id)
    if not review or review.is_deleted:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this review",
        )

    updated = await review_service.update_review(db, review=review, data=payload)
    fresh = await review_repository.get_by_id(db, updated.id)
    return ReviewResponse.model_validate(fresh)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete your own review or reply",
)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review: Review | None = await review_repository.get_by_id(db, review_id)
    if not review or review.is_deleted:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review",
        )

    await review_service.delete_review(db, review=review)
