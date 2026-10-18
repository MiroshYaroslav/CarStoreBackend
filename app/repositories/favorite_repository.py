import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite
from app.models.product import Product
from app.repositories.base import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    _model = Favorite

    async def get_user_favorites(self, user_id: uuid.UUID):
        query = (
            select(Favorite)
            .options(
                selectinload(Favorite.product).selectinload(Product.engines),
                selectinload(Favorite.product).selectinload(Product.colors),
                selectinload(Favorite.product).selectinload(Product.trims),
            )
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        result = await self._require_session().execute(query)
        return result.scalars().all()

    async def get_by_user_and_product(self, user_id: uuid.UUID, product_id: uuid.UUID):
        query = select(Favorite).where(
            and_(Favorite.user_id == user_id, Favorite.product_id == product_id)
        )
        result = await self._require_session().execute(query)
        return result.scalars().first()

    async def get_with_product(self, favorite_id: uuid.UUID) -> Favorite | None:
        query = (
            select(Favorite)
            .options(
                selectinload(Favorite.product).selectinload(Product.engines),
                selectinload(Favorite.product).selectinload(Product.colors),
                selectinload(Favorite.product).selectinload(Product.trims),
            )
            .where(Favorite.id == favorite_id)
        )
        result = await self._require_session().execute(query)
        return result.scalars().first()
