import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BasePydanticModel
from app.schemas.product import ColorRead, EngineRead, ProductRead, TrimRead


class CartItemBase(BasePydanticModel):
    product_id: uuid.UUID
    engine_id: uuid.UUID | None = None
    color_id: uuid.UUID | None = None
    trim_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1)


class CartItemCreate(CartItemBase):
    session_id: str | None = None


class CartItemUpdate(BasePydanticModel):
    quantity: int = Field(ge=1)


class CartItemRead(CartItemBase):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    session_id: str | None = None
    created_at: datetime
    updated_at: datetime

    product: ProductRead | None = None
    engine: EngineRead | None = None
    color: ColorRead | None = None
    trim: TrimRead | None = None
