import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.schemas.order import OrderCreate
from app.services.base import BaseService


class OrderService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        orders: OrderRepository,
        items: OrderItemRepository,
        cart: CartRepository,
    ):
        super().__init__(session)
        self._orders, self._items, self._cart = orders, items, cart

    async def create_order(self, order_in: OrderCreate, user_id: uuid.UUID | None = None):
        if not user_id and not order_in.session_id:
            raise HTTPException(status_code=400, detail="Must provide user_id or session_id")
        cart_items = await self._cart.get_cart(
            user_id=user_id, session_id=order_in.session_id if not user_id else None
        )
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        total_price = Decimal("0.00")
        order_items = []
        for item in cart_items:
            unit_price = item.product.base_price
            snapshot = {"product_name": item.product.name}
            for relation, label in (
                (item.engine, "engine"),
                (item.color, "color"),
                (item.trim, "trim"),
            ):
                if relation:
                    unit_price += relation.price_modifier
                    snapshot[f"{label}_name"] = relation.name
            total_price += unit_price * item.quantity
            order_items.append(
                {
                    "product_id": item.product_id,
                    "engine_id": item.engine_id,
                    "color_id": item.color_id,
                    "trim_id": item.trim_id,
                    "quantity": item.quantity,
                    "price_per_unit": unit_price,
                    "configuration_snapshot": snapshot,
                }
            )
        try:
            order_data = order_in.model_dump(exclude={"session_id"})
            order_data.update(user_id=user_id, total_price=total_price)
            order = await self._orders.create(order_data)
            for item_data in order_items:
                item_data["order_id"] = order.id
                await self._items.create(item_data)
            for item in cart_items:
                await self._cart.delete(item.id)
            result = await self._orders.get_order_with_items(order.id)
            if result is None:
                raise NotFoundException("Order not found after creation")
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Order conflicts with existing data")

    async def list_user_orders(self, user_id: uuid.UUID):
        return await self._orders.get_user_orders(user_id)
