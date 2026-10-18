import uuid
from datetime import datetime

from pydantic import EmailStr

from app.schemas.base import BasePydanticModel


class UserBase(BasePydanticModel):
    email: EmailStr
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BasePydanticModel):
    email: EmailStr | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None


class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
