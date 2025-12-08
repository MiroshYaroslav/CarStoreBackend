from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class EngineBase(BaseModel):
    name: str
    volume: float
    power: int
    acceleration: float
    top_speed: Optional[int] = None
    price_modifier: float = 0
    fuel_type: Optional[str] = "Petrol"

class EngineCreate(EngineBase):
    pass

class EngineRead(EngineBase):
    id: int
    model_config = {"from_attributes": True}


class ColorBase(BaseModel):
    name: str
    hex_code: Optional[str] = None
    price_modifier: float = 0
    image_url: Optional[str] = None

class ColorCreate(ColorBase):
    pass

class ColorRead(ColorBase):
    id: int
    model_config = {"from_attributes": True}


class TrimBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_modifier: float = 0

class TrimCreate(TrimBase):
    pass

class TrimRead(TrimBase):
    id: int
    model_config = {"from_attributes": True}


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryRead(CategoryBase):
    id: int
    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    category_id: Optional[int] = None
    image: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    category_id: Optional[int] = None
    image: Optional[str] = None

class ProductRead(ProductBase):
    id: int
    engines: List[EngineRead] = []
    colors: List[ColorRead] = []
    trims: List[TrimRead] = []

    model_config = {"from_attributes": True}


class ReviewBase(BaseModel):
    product_id: int
    username: str
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    username: Optional[str] = None
    rating: Optional[int] = None
    comment: Optional[str] = None

class ReviewRead(ReviewBase):
    id: int
    created_at: Optional[datetime]
    model_config = {"from_attributes": True}


class PhoneNumberBase(BaseModel):
    number: str
    description: Optional[str] = None

class PhoneNumberCreate(PhoneNumberBase):
    pass

class PhoneNumberUpdate(BaseModel):
    number: Optional[str] = None
    description: Optional[str] = None

class PhoneNumberRead(PhoneNumberBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    email: str
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password_hash: Optional[str] = None

class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
    first_name: str | None = None
    last_name: str | None = None


class FavoriteBase(BaseModel):
    user_id: int
    product_id: int

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteUpdate(BaseModel):
    user_id: Optional[int] = None
    product_id: Optional[int] = None

class FavoriteRead(FavoriteBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class CartItemBase(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1
    engine_id: Optional[int] = None
    color_id: Optional[int] = None
    trim_id: Optional[int] = None

class CartItemCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1
    engine_id: Optional[int] = None
    color_id: Optional[int] = None
    trim_id: Optional[int] = None

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None

class CartItemRead(CartItemBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    product: Optional[ProductBase] = None
    engine: Optional[EngineRead] = None
    color: Optional[ColorRead] = None
    trim: Optional[TrimRead] = None

    model_config = {"from_attributes": True}

class OrderCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str

class OrderItemRead(BaseModel):
    id: int
    product: ProductRead
    engine: EngineRead | None = None
    color: ColorRead | None = None
    trim: TrimRead | None = None
    quantity: int
    price_per_unit: float

    model_config = ConfigDict(from_attributes=True)

class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: str
    total_price: float
    first_name: str
    last_name: str
    phone: str
    address: str
    items: list[OrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)