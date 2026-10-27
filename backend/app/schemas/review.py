from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReviewBase(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: str) -> str:
        return v.strip()


class ReviewCreateRequest(ReviewBase):
    rating: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Required for top-level reviews; optional for replies.",
    )
    parent_review_id: UUID | None = Field(
        None,
        description=(
            "ID of the review this is a reply to. "
            "Leave null for a top-level review. "
            "Only one level of nesting is allowed."
        ),
    )

    @model_validator(mode="after")
    def rating_required_for_top_level(self) -> ReviewCreateRequest:
        if self.parent_review_id is None and self.rating is None:
            raise ValueError("rating is required for top-level reviews")
        return self


class ReviewUpdateRequest(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(
        None, min_length=1, max_length=1000, description="New comment text"
    )

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v


class ReviewReplyResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str | None = None
    user_name: str | None = None
    event_id: UUID
    parent_review_id: UUID
    rating: int | None = None
    comment: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str | None = None
    user_name: str | None = None
    event_id: UUID
    parent_review_id: UUID | None = None
    rating: int | None = None
    comment: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime | None = None
    replies: list[ReviewReplyResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    skip: int
    limit: int
