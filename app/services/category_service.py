import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.base import BaseService


class CategoryService(BaseService):
    def __init__(self, session: AsyncSession, repository: CategoryRepository):
        super().__init__(session)
        self._repository = repository

    async def list_categories(self) -> list[Category]:
        return await self._repository.get_many()

    async def create_category(self, category_in: CategoryCreate) -> Category:
        try:
            result = await self._repository.create(category_in.model_dump())
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Category conflicts with existing data")

    async def update_category(
        self, category_id: uuid.UUID, category_in: CategoryUpdate
    ) -> Category:
        try:
            result = await self._repository.update(
                category_id, category_in.model_dump(exclude_unset=True)
            )
            if not result:
                raise NotFoundException("Category not found")
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Category conflicts with existing data")

    async def delete_category(self, category_id: uuid.UUID, hard_delete: bool = False) -> None:
        category = await self._repository.get(category_id)
        if not category:
            raise NotFoundException("Category not found")
        try:
            if hard_delete:
                if await self._repository.has_products(category_id):
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot hard delete category with associated products",
                    )
                await self._repository.delete(category_id)
            else:
                await self._repository.update(category_id, {"is_active": False})
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
