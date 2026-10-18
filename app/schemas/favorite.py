import uuid
from datetime import datetime

from app.schemas.base import BasePydanticModel
from app.schemas.product import ProductRead


class FavoriteBase(BasePydanticModel):
    product_id: uuid.UUID


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteRead(FavoriteBase):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    product: ProductRead | None = None
