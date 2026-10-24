from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    model = Review

    async def get_by_id(self, db: AsyncSession, review_id: UUID) -> Review | None:
        query = (
            select(Review)
            .options(selectinload(Review.replies))
            .where(Review.id == review_id, Review.is_deleted.is_(False))
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def list_by_event(self, db: AsyncSession, event_id: UUID, skip: int = 0, limit: int = 20):
        query = (
            select(Review)
            .where(Review.event_id == event_id, Review.is_deleted.is_(False))
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        items = result.scalars().all()
        count_stmt = select(func.count()).select_from(Review).where(Review.event_id == event_id, Review.is_deleted.is_(False))
        total = (await db.execute(count_stmt)).scalar_one()
        return items, total

    async def create(
        self,
        db: AsyncSession,
        *,
        event_id: UUID,
        user_id: UUID,
        rating: int | None = None,
        comment: str,
        parent_review_id: UUID | None = None,
    ) -> Review:
        review = Review(
            event_id=event_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            parent_review_id=parent_review_id,
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def list_top_level(
        self, db: AsyncSession, event_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Review], int]:
        query = (
            select(Review)
            .options(selectinload(Review.replies))
            .where(
                Review.event_id == event_id,
                Review.is_deleted.is_(False),
                Review.parent_review_id.is_(None),
            )
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        items = result.scalars().unique().all()

        count_stmt = (
            select(func.count())
            .select_from(Review)
            .where(
                Review.event_id == event_id,
                Review.is_deleted.is_(False),
                Review.parent_review_id.is_(None),
            )
        )
        total = (await db.execute(count_stmt)).scalar_one()
        return items, total

    async def update(self, db: AsyncSession, review: Review, *, rating: int | None = None, comment: str | None = None) -> Review:
        if rating is not None:
            review.rating = rating
        if comment is not None:
            review.comment = comment
        await db.commit()
        await db.refresh(review)
        return review

    async def soft_delete(self, db: AsyncSession, review: Review) -> None:
        review.is_deleted = True
        await db.commit()


review_repository = ReviewRepository()  