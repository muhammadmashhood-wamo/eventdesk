# app/api/v1/reviews.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.review import Review
from app.models.user import User
from app.repositories.review_repository import review_repository
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewReplyResponse,
    ReviewResponse,
    ReviewUpdateRequest,
)
from app.services.review_service import review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _build_nested(reviews: list[Review]) -> list[ReviewResponse]:
    """
    Given a flat list of top-level reviews (already filtered by the repository),
    attach their non-deleted replies and return nested ReviewResponse objects.
    """
    result: list[ReviewResponse] = []
    for parent in reviews:
        parent_resp = ReviewResponse.from_orm(parent)
        # SQLAlchemy has already loaded `parent.replies` via the relationship
        parent_resp.replies = [
            ReviewReplyResponse.from_orm(r)
            for r in parent.replies
            if not r.is_deleted
        ]
        result.append(parent_resp)
    return result


# -----------------------------------------------------------------
# CREATE  (top-level OR reply)
# -----------------------------------------------------------------
@router.post(
    "/events/{event_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review or a reply to a review for an event",
)
async def create_review(
    event_id: UUID,
    payload: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = await review_service.create_review(
        db,
        event_id=event_id,
        user_id=current_user.id,
        data=payload,
    )
    # Re-fetch so that the `replies` relationship is populated (empty list for new review)
    fresh = await review_repository.get_by_id(db, review.id)
    return ReviewResponse.from_orm(fresh)


# -----------------------------------------------------------------
# LIST (top-level reviews + their replies, paginated)
# -----------------------------------------------------------------
@router.get(
    "/events/{event_id}",
    response_model=list[ReviewResponse],
    summary="List reviews for an event (top-level with replies nested)",
)
async def list_reviews(
    event_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    reviews, _ = await review_service.list_by_event(
        db, event_id=event_id, skip=skip, limit=limit
    )
    return _build_nested(reviews)


# -----------------------------------------------------------------
# UPDATE
# -----------------------------------------------------------------
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

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this review",
        )

    updated = await review_service.update_review(db, review=review, data=payload)
    fresh = await review_repository.get_by_id(db, updated.id)
    return ReviewResponse.from_orm(fresh)


# -----------------------------------------------------------------
# DELETE (soft-delete)
# -----------------------------------------------------------------
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

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review",
        )

    await review_service.delete_review(db, review=review)
