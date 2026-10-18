import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BasePydanticModel


class ReviewBase(BasePydanticModel):
    product_id: uuid.UUID
    username: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BasePydanticModel):
    username: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = None


class ReviewRead(ReviewBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
