import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.product import Product
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[CartItem]):
    _model = CartItem

    async def get_cart(self, user_id: uuid.UUID | None = None, session_id: str | None = None):
        query = select(CartItem).options(
            selectinload(CartItem.product).selectinload(Product.engines),
            selectinload(CartItem.product).selectinload(Product.colors),
            selectinload(CartItem.product).selectinload(Product.trims),
            selectinload(CartItem.engine),
            selectinload(CartItem.color),
            selectinload(CartItem.trim),
        )
        if user_id:
            query = query.where(CartItem.user_id == user_id)
        elif session_id:
            query = query.where(CartItem.session_id == session_id)
        else:
            return []

        query = query.order_by(CartItem.created_at.desc())
        result = await self._require_session().execute(query)
        return result.scalars().all()

    async def get_item_by_params(
        self,
        user_id: uuid.UUID | None,
        session_id: str | None,
        product_id: uuid.UUID,
        engine_id: uuid.UUID | None,
        color_id: uuid.UUID | None,
        trim_id: uuid.UUID | None,
    ):
        query = select(CartItem).where(
            and_(
                CartItem.product_id == product_id,
                CartItem.engine_id == engine_id,
                CartItem.color_id == color_id,
                CartItem.trim_id == trim_id,
            )
        )
        if user_id:
            query = query.where(CartItem.user_id == user_id)
        elif session_id:
            query = query.where(CartItem.session_id == session_id)

        result = await self._require_session().execute(query)
        return result.scalars().first()

    async def get_item_with_relations(self, item_id: uuid.UUID) -> CartItem | None:
        query = (
            select(CartItem)
            .options(
                selectinload(CartItem.product).selectinload(Product.engines),
                selectinload(CartItem.product).selectinload(Product.colors),
                selectinload(CartItem.product).selectinload(Product.trims),
                selectinload(CartItem.engine),
                selectinload(CartItem.color),
                selectinload(CartItem.trim),
            )
            .where(CartItem.id == item_id)
        )
        result = await self._require_session().execute(query)
        return result.scalars().first()
