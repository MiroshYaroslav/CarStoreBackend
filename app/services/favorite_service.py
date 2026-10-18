import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.favorite import FavoriteCreate
from app.services.base import BaseService


class FavoriteService(BaseService):
    def __init__(
        self, session: AsyncSession, repository: FavoriteRepository, products: ProductRepository
    ):
        super().__init__(session)
        self._repository, self._products = repository, products

    async def list_favorites(self, user_id: uuid.UUID):
        return await self._repository.get_user_favorites(user_id)

    async def add_favorite(self, user_id: uuid.UUID, favorite_in: FavoriteCreate):
        if not await self._products.get_with_relations(favorite_in.product_id):
            raise NotFoundException("Product not found")
        if await self._repository.get_by_user_and_product(user_id, favorite_in.product_id):
            raise HTTPException(status_code=400, detail="Product already in favorites")
        try:
            result = await self._repository.create(
                {"user_id": user_id, "product_id": favorite_in.product_id}
            )
            result = await self._repository.get_with_product(result.id)
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Favorite conflicts with existing data")

    async def remove_favorite(self, user_id: uuid.UUID, favorite_id: uuid.UUID) -> None:
        try:
            favorite = await self._repository.get(favorite_id)
            if not favorite or favorite.user_id != user_id:
                raise NotFoundException("Favorite not found")
            await self._repository.delete(favorite_id)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
