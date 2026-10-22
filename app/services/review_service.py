from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.repositories.review_repository import review_repository
from app.schemas.review import ReviewCreateRequest, ReviewUpdateRequest


class ReviewService:

    async def create_review(
        self,
        db: AsyncSession,
        *,
        event_id: UUID,
        user_id: UUID,
        data: ReviewCreateRequest,
    ) -> Review:
        if data.parent_review_id is not None:
            parent = await review_repository.get_by_id(db, data.parent_review_id)
            if not parent or parent.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent review not found",
                )
            if parent.parent_review_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only one level of replies is allowed",
                )
            if parent.event_id != event_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent review does not belong to this event",
                )

        return await review_repository.create(
            db,
            event_id=event_id,
            user_id=user_id,
            rating=data.rating,
            comment=data.comment,
            parent_review_id=data.parent_review_id,
        )

    async def list_by_event(
        self,
        db: AsyncSession,
        *,
        event_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Review], int]:
        return await review_repository.list_top_level(
            db, event_id=event_id, skip=skip, limit=limit
        )

    async def update_review(
        self,
        db: AsyncSession,
        *,
        review: Review,
        data: ReviewUpdateRequest,
    ) -> Review:
        return await review_repository.update(
            db,
            review,
            rating=data.rating,
            comment=data.comment,
        )

    async def delete_review(
        self,
        db: AsyncSession,
        *,
        review: Review,
    ) -> None:
        await review_repository.soft_delete(db, review)


review_service = ReviewService()
