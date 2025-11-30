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

class UserBase(BaseModel):
    email: str
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password_hash: Optional[str] = None

class UserRead(UserBase):
    id: int
    created_at: Optional[datetime.datetime] = None
    model_config = {"from_attributes": True}

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
    created_at: Optional[datetime.datetime] = None
    model_config = {"from_attributes": True}
