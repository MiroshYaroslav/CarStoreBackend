import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models import Product
from app.models.product import Product
from app.repositories.product_repository import (
    ColorRepository,
    EngineRepository,
    ProductRepository,
    TrimRepository,
)
from app.schemas.product import ColorCreate, EngineCreate, TrimCreate
from app.services.base import BaseService


class ProductService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        products: ProductRepository,
        engines: EngineRepository,
        colors: ColorRepository,
        trims: TrimRepository,
    ):
        super().__init__(session)
        self._products, self._engines, self._colors, self._trims = products, engines, colors, trims

    async def list_products(self, **filters):
        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(status_code=422, detail="min_price must not exceed max_price")
        return await self._products.get_multi_filtered(**filters)

    async def get_product_or_404(self, product_id: uuid.UUID) -> Product:
        product = await self._products.get_with_relations(product_id)
        if not product:
            raise NotFoundException("Product not found")
        return product

    async def _add_option(self, repository, product_id: uuid.UUID, payload):
        await self.get_product_or_404(product_id)
        try:
            result = await repository.create({**payload.model_dump(), "product_id": product_id})
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Product option conflicts with existing data")

    async def add_engine(self, product_id: uuid.UUID, engine_in: EngineCreate):
        return await self._add_option(self._engines, product_id, engine_in)

    async def add_color(self, product_id: uuid.UUID, color_in: ColorCreate):
        return await self._add_option(self._colors, product_id, color_in)

    async def add_trim(self, product_id: uuid.UUID, trim_in: TrimCreate):
        return await self._add_option(self._trims, product_id, trim_in)

    async def soft_delete(self, product_id: uuid.UUID):
        await self.get_product_or_404(product_id)
        try:
            result = await self._products.update(product_id, {"is_active": False})
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise

    async def update_product_image(self, product_id: uuid.UUID, image_url: str) -> Product | None:
        await self.get_product_or_404(product_id)
        try:
            await self._products.update(product_id, {"image_url": image_url})
            await self._session.commit()
            # The commit expires ORM instances by default. Reload the product
            # with its response relationships before FastAPI serializes ProductRead.
            return await self.get_product_or_404(product_id)
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Failed to update product image")
