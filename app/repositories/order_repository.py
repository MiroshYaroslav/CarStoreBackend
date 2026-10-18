import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    _model = Order

    async def get_user_orders(self, user_id: uuid.UUID):
        query = (
            select(Order)
            .options(
                selectinload(Order.items).options(
                    selectinload(OrderItem.product).selectinload(Product.engines),
                    selectinload(OrderItem.product).selectinload(Product.colors),
                    selectinload(OrderItem.product).selectinload(Product.trims),
                    selectinload(OrderItem.engine),
                    selectinload(OrderItem.color),
                    selectinload(OrderItem.trim),
                )
            )
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )

        result = await self._require_session().execute(query)
        return result.scalars().unique().all()

    async def get_order_with_items(self, order_id: uuid.UUID):
        query = (
            select(Order)
            .options(
                selectinload(Order.items).options(
                    selectinload(OrderItem.product).selectinload(Product.engines),
                    selectinload(OrderItem.product).selectinload(Product.colors),
                    selectinload(OrderItem.product).selectinload(Product.trims),
                    selectinload(OrderItem.engine),
                    selectinload(OrderItem.color),
                    selectinload(OrderItem.trim),
                )
            )
            .where(Order.id == order_id)
        )
        result = await self._require_session().execute(query)
        return result.scalars().first()


class OrderItemRepository(BaseRepository[OrderItem]):
    _model = OrderItem
