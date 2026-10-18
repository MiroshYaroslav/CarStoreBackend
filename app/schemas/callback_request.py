import uuid
from datetime import datetime

from app.schemas.base import BasePydanticModel


class CallbackRequestBase(BasePydanticModel):
    name: str | None = None
    phone: str
    description: str | None = None


class CallbackRequestCreate(CallbackRequestBase):
    pass


class CallbackRequestUpdate(BasePydanticModel):
    status: str


class CallbackRequestRead(CallbackRequestBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
