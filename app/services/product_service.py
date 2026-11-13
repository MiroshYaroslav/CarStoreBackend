import asyncio
import hashlib
import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException, Response
from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.repositories.product_repository import (
    ColorRepository,
    EngineRepository,
    ProductRepository,
    TrimRepository,
)
from app.schemas.product import ColorCreate, EngineCreate, ProductRead, TrimCreate
from app.services.base import BaseService

logger = logging.getLogger("bmw_api")


class ProductService(BaseService):
    def __init__(
            self,
            session: AsyncSession,
            products: ProductRepository,
            engines: EngineRepository,
            colors: ColorRepository,
            trims: TrimRepository,
            redis: Redis,
            cache_enabled: bool = True,
    ):
        super().__init__(session)
        self._products = products
        self._engines = engines
        self._colors = colors
        self._trims = trims
        self._redis = redis
        self._cache_enabled = cache_enabled

    async def ensure_exists(self, product_id: uuid.UUID) -> None:
        product = await self._products.get_with_relations(product_id)
        if not product:
            raise NotFoundException("Product not found")

    @staticmethod
    async def _serialize_in_executor(data: Any) -> str:
        def serialize():
            if isinstance(data, list):
                dumped = [ProductRead.model_validate(p).model_dump(mode='json') for p in data]
                return json.dumps(dumped)

            return ProductRead.model_validate(data).model_dump_json()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, serialize)

    async def _invalidate_product_cache(self, product_id: uuid.UUID | None = None) -> None:
        if not self._cache_enabled:
            return
        patterns = ["catalog:products:v1:*"]
        if product_id:
            patterns.append(f"catalog:product:{product_id}")

        for pattern in patterns:
            try:
                keys = [key async for key in self._redis.scan_iter(match=pattern, count=100)]
                if keys:
                    await self._redis.unlink(*keys)
            except RedisError as e:
                logger.error(f"Failed to invalidate cache for pattern {pattern}: {e}")

    async def list_products(self, **filters) -> Response:
        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(status_code=422, detail="min_price must not exceed max_price")

        canonical_filters = json.dumps(
            {k: str(v) if v is not None else None for k, v in sorted(filters.items())},
            sort_keys=True,
        )
        cache_key = f"catalog:products:v1:{hashlib.sha256(canonical_filters.encode()).hexdigest()}"

        if self._cache_enabled:
            try:
                cached_data = await self._redis.get(cache_key)
                if cached_data is not None:
                    try:
                        await self._redis.incr("catalog:metrics:products:hits")
                    except RedisError:
                        pass
                    return Response(content=cached_data, media_type="application/json")
            except RedisError as e:
                logger.warning(f"Redis GET failed for list_products: {e}")

            try:
                await self._redis.incr("catalog:metrics:products:misses")
            except RedisError:
                pass

        products = await self._products.get_multi_filtered(**filters)
        serialized_data = await self._serialize_in_executor(products)

        if self._cache_enabled:
            try:
                await self._redis.set(cache_key, serialized_data, ex=60)
            except RedisError as e:
                logger.warning(f"Redis SET failed for list_products: {e}")

        return Response(content=serialized_data, media_type="application/json")

    async def get_product_or_404(self, product_id: uuid.UUID) -> Response:
        cache_key = f"catalog:product:{product_id}"

        if self._cache_enabled:
            try:
                cached_data = await self._redis.get(cache_key)
                if cached_data is not None:
                    return Response(content=cached_data, media_type="application/json")
            except RedisError as e:
                logger.warning(f"Redis GET failed for get_product_or_404: {e}")

        product = await self._products.get_with_relations(product_id)
        if not product:
            raise NotFoundException("Product not found")

        serialized_data = await self._serialize_in_executor(product)

        if self._cache_enabled:
            try:
                await self._redis.set(cache_key, serialized_data, ex=60)
            except RedisError as e:
                logger.warning(f"Redis SET failed for get_product_or_404: {e}")

        return Response(content=serialized_data, media_type="application/json")

    async def _add_option(self, repository: Any, product_id: uuid.UUID, payload: Any):
        await self.ensure_exists(product_id)
        try:
            result = await repository.create({**payload.model_dump(), "product_id": product_id})
            await self._session.commit()
            await self._invalidate_product_cache(product_id)
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
        await self.ensure_exists(product_id)
        try:
            result = await self._products.update(product_id, {"is_active": False})
            await self._session.commit()
            await self._invalidate_product_cache(product_id)
            return result
        except IntegrityError:
            await self._session.rollback()
            raise

    async def update_product_image(self, product_id: uuid.UUID, image_url: str) -> Response:
        await self.ensure_exists(product_id)
        try:
            await self._products.update(product_id, {"image_url": image_url})
            await self._session.commit()
            await self._invalidate_product_cache(product_id)
            return await self.get_product_or_404(product_id)
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Failed to update product image")