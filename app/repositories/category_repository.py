import uuid

from sqlalchemy import select

from app.models.category import Category
from app.models.product import Product
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    _model = Category

    async def has_products(self, category_id: uuid.UUID) -> bool:
        result = await self._require_session().execute(
            select(Product.id).where(Product.category_id == category_id).limit(1)
        )
        return result.first() is not None
