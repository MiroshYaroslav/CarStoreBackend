from typing import Optional
from pydantic import BaseModel

class Car(BaseModel):
    id: Optional[int] = None
    brand: Optional[str] = None
    year: Optional[int] = None
    power: Optional[int] = None
    price: Optional[float] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    username: str
    password: str
    admin_code: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str
