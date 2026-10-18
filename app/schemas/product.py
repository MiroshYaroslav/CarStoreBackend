import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BasePydanticModel


# --- Engines ---
class EngineBase(BasePydanticModel):
    name: str
    volume: float
    power: int
    acceleration: float
    top_speed: int | None = None
    price_modifier: Decimal = Decimal("0.00")
    fuel_type: str | None = "Petrol"


class EngineCreate(EngineBase):
    pass


class EngineRead(EngineBase):
    id: uuid.UUID


# --- Colors ---
class ColorBase(BasePydanticModel):
    name: str
    hex_code: str | None = None
    price_modifier: Decimal = Decimal("0.00")
    image_url: str | None = None


class ColorCreate(ColorBase):
    pass


class ColorRead(ColorBase):
    id: uuid.UUID


# --- Trims ---
class TrimBase(BasePydanticModel):
    name: str
    description: str | None = None
    price_modifier: Decimal = Decimal("0.00")


class TrimCreate(TrimBase):
    pass


class TrimRead(TrimBase):
    id: uuid.UUID


# --- Products ---
class ProductBase(BasePydanticModel):
    name: str
    description: str | None = None
    base_price: Decimal
    category_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BasePydanticModel):
    name: str | None = None
    description: str | None = None
    base_price: Decimal | None = None
    category_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ProductRead(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    engines: list[EngineRead] = Field(default_factory=list)
    colors: list[ColorRead] = Field(default_factory=list)
    trims: list[TrimRead] = Field(default_factory=list)
