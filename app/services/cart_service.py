import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models.cart import CartItem
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemCreate
from app.services.base import BaseService


class CartService(BaseService):
    def __init__(
        self, session: AsyncSession, repository: CartRepository, products: ProductRepository
    ):
        super().__init__(session)
        self._repository, self._products = repository, products

    async def add_to_cart(
        self, item_in: CartItemCreate, user_id: uuid.UUID | None = None
    ) -> CartItem:
        if not user_id and not item_in.session_id:
            raise HTTPException(
                status_code=400, detail="Must provide either auth token or session_id"
            )
        if not await self._products.get_with_relations(item_in.product_id):
            raise NotFoundException("Product not found")
        existing = await self._repository.get_item_by_params(
            user_id,
            item_in.session_id if not user_id else None,
            item_in.product_id,
            item_in.engine_id,
            item_in.color_id,
            item_in.trim_id,
        )
        try:
            if existing:
                result = await self._repository.update(
                    existing.id, {"quantity": existing.quantity + item_in.quantity}
                )
            else:
                data = item_in.model_dump()
                data["user_id"] = user_id
                if user_id:
                    data["session_id"] = None
                result = await self._repository.create(data)
            if result is None:
                raise NotFoundException("Cart item not found")
            result = await self._repository.get_item_with_relations(result.id)
            if result is None:
                raise NotFoundException("Cart item not found")
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Cart item conflicts with existing data")

    async def get_cart(self, user_id: uuid.UUID | None = None, session_id: str | None = None):
        return await self._repository.get_cart(user_id=user_id, session_id=session_id)

    async def remove_item(
        self, item_id: uuid.UUID, user_id: uuid.UUID | None = None, session_id: str | None = None
    ) -> None:
        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="Must provide either auth token or session_id"
            )
        try:
            if not await self._repository.get_owned_item(item_id, user_id, session_id):
                raise NotFoundException("Cart item not found")
            await self._repository.delete(item_id)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
