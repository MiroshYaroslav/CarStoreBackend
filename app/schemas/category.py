import uuid
from datetime import datetime

from app.schemas.base import BasePydanticModel


class CategoryBase(BasePydanticModel):
    name: str
    description: str | None = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BasePydanticModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryRead(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
