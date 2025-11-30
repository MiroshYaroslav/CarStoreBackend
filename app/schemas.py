from pydantic import BaseModel
from typing import Optional
import datetime

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
    price: float
    category_id: Optional[int] = None

    power: Optional[int] = None
    top_speed: Optional[int] = None
    acceleration: Optional[float] = None

    image: Optional[str] = None


class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    power: Optional[int] = None
    top_speed: Optional[int] = None
    acceleration: Optional[float] = None
    image: Optional[str] = None


class ProductRead(ProductBase):
    id: int

    model_config = {
        "from_attributes": True
    }


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
    created_at: Optional[datetime.datetime]
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
    created_at: Optional[datetime.datetime] = None
    model_config = {"from_attributes": True}
