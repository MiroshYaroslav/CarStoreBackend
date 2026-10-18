import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import EmailStr, Field

from app.schemas.base import BasePydanticModel
from app.schemas.product import ColorRead, EngineRead, ProductRead, TrimRead


class OrderCreate(BasePydanticModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address: str
    session_id: str | None = None


class OrderItemRead(BasePydanticModel):
    id: uuid.UUID
    product_id: uuid.UUID | None = None
    quantity: int
    price_per_unit: Decimal
    configuration_snapshot: dict[str, Any] | None = None

    product: ProductRead | None = None
    engine: EngineRead | None = None
    color: ColorRead | None = None
    trim: TrimRead | None = None


class OrderRead(BasePydanticModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    status: str
    total_price: Decimal
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    created_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)
