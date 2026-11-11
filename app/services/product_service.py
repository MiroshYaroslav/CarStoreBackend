import uuid
import json
import hashlib
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.exceptions.base import ConflictException, NotFoundException
from app.models.product import Product
from app.repositories.product_repository import (
    ColorRepository,
    EngineRepository,
    ProductRepository,
    TrimRepository,
)
from app.schemas.product import ColorCreate, EngineCreate, TrimCreate, ProductRead
from app.services.base import BaseService


class ProductService(BaseService):
    def __init__(
            self,
            session: AsyncSession,
            products: ProductRepository,
            engines: EngineRepository,
            colors: ColorRepository,
            trims: TrimRepository,
            redis: Redis,
    ):
        super().__init__(session)
        self._products = products
        self._engines = engines
        self._colors = colors
        self._trims = trims
        self._redis = redis

    async def list_products(self, **filters):
        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(status_code=422, detail="min_price must not exceed max_price")

        canonical_filters = json.dumps(
            {k: str(v) if v is not None else None for k, v in sorted(filters.items())},
            sort_keys=True
        )
        cache_key = f"catalog:products:v1:{hashlib.sha256(canonical_filters.encode()).hexdigest()}"

        try:
            cached_data = await self._redis.get(cache_key)
            if cached_data is not None:
                return [ProductRead.model_validate(item) for item in json.loads(cached_data)]
        except RedisError:
            pass

        products = await self._products.get_multi_filtered(**filters)

        payload = [
            ProductRead.model_validate(p).model_dump(mode="json")
            for p in products
        ]
        try:
            await self._redis.set(cache_key, json.dumps(payload), ex=60)
        except RedisError:
            pass

        return products

    async def get_product_or_404(self, product_id: uuid.UUID) -> Product | ProductRead:
        cache_key = f"catalog:product:{product_id}"

        try:
            cached_data = await self._redis.get(cache_key)
            if cached_data is not None:
                return ProductRead.model_validate(json.loads(cached_data))
        except RedisError:
            pass

        product = await self._products.get_with_relations(product_id)
        if not product:
            raise NotFoundException("Product not found")

        payload = ProductRead.model_validate(product).model_dump(mode="json")
        try:
            await self._redis.set(cache_key, json.dumps(payload), ex=300)  # TTL 5 хвилин
        except RedisError:
            pass

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
            return await self.get_product_or_404(product_id)
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Failed to update product image")
