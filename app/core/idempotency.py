import json
from collections.abc import Awaitable, Callable
from typing import Annotated, TypeVar

from fastapi import Depends, Header, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis

from app.core.redis import get_redis_client

IDEMPOTENCY_TTL_SECONDS = 86400
LOCK_TTL_SECONDS = 60

T = TypeVar("T")


class IdempotencyHandler:
    def __init__(self, redis: Redis | None, key: str | None):
        self._redis = redis
        self._redis_key = f"idempotency:{key.strip()}" if key and key.strip() else None
        self._is_cached = False

    async def acquire(self) -> dict | None:
        if not self._redis or not self._redis_key:
            return None

        acquired = await self._redis.set(
            self._redis_key,
            json.dumps({"state": "PROCESSING"}),
            nx=True,
            ex=LOCK_TTL_SECONDS,
        )
        if acquired:
            return None

        raw = await self._redis.get(self._redis_key)
        if not raw:
            return None

        data = json.loads(raw)
        if data.get("state") == "PROCESSING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request with this Idempotency-Key is already in progress",
            )

        self._is_cached = True
        return data

    async def save(self, status_code: int, body: object) -> None:
        if not self._redis or not self._redis_key:
            return

        payload = {
            "state": "COMPLETED",
            "status_code": status_code,
            "body": jsonable_encoder(body),
        }
        await self._redis.set(
            self._redis_key,
            json.dumps(payload),
            ex=IDEMPOTENCY_TTL_SECONDS,
        )

    async def release_on_error(self) -> None:
        if self._redis and self._redis_key and not self._is_cached:
            await self._redis.delete(self._redis_key)

    async def execute(
        self,
        response: Response,
        status_code: int,
        action: Callable[[], Awaitable[T]],
    ) -> T | dict:
        cached = await self.acquire()
        if cached:
            response.status_code = cached["status_code"]
            return cached["body"]

        try:
            result = await action()
            await self.save(status_code, result)
            return result
        except Exception:
            await self.release_on_error()
            raise


async def get_idempotency_handler(
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> IdempotencyHandler:
    redis_client = getattr(request.app.state, "redis", None) or get_redis_client()
    return IdempotencyHandler(redis=redis_client, key=idempotency_key)


IdempotencyDep = Annotated[IdempotencyHandler, Depends(get_idempotency_handler)]

