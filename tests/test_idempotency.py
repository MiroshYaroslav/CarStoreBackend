import uuid
from typing import cast

import pytest
from fastapi import Header
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import delete, func, select

from app.core.config import settings
from app.core.database import AsyncSessionMaker, engine
from app.core.idempotency import IdempotencyHandler, get_idempotency_handler
from app.main import app
from app.models.async_task import AsyncTask
from app.services import callback_request_service


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(
        self, key: str, value: str, nx: bool = False, ex: int | None = None
    ) -> bool:
        _ = ex
        if nx and key in self._store:
            return False
        self._store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class FakeSQSClient:
    def send_message(self, **_: object) -> dict[str, str]:
        return {"MessageId": "1"}


@pytest.mark.asyncio
async def test_idempotency_single_db_record_and_identical_responses(
    monkeypatch: pytest.MonkeyPatch,
):
    fake_redis = FakeRedis()

    async def override_idempotency(
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> IdempotencyHandler:
        return IdempotencyHandler(redis=cast(Redis, fake_redis), key=idempotency_key)

    app.dependency_overrides[get_idempotency_handler] = override_idempotency
    monkeypatch.setattr(callback_request_service, "sqs_client", FakeSQSClient())

    original_sqs_url = settings.SQS_QUEUE_URL
    settings.SQS_QUEUE_URL = "https://sqs.eu-central-1.amazonaws.com/000/test"

    headers = {"Idempotency-Key": str(uuid.uuid4())}
    payload = {"name": "Yaroslav", "phone": "+380991234567"}
    created_task_id: uuid.UUID | None = None

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res1 = await client.post(
                "/api/v1/callback-requests/async", json=payload, headers=headers
            )
            res2 = await client.post(
                "/api/v1/callback-requests/async", json=payload, headers=headers
            )

        assert res1.status_code == 202
        assert res2.status_code == 202
        assert res1.json() == res2.json()

        created_task_id = uuid.UUID(res1.json()["task_id"])

        async with AsyncSessionMaker() as db:
            count_result = await db.execute(
                select(func.count())
                .select_from(AsyncTask)
                .where(AsyncTask.id == created_task_id)
            )
            assert count_result.scalar_one() == 1
    finally:
        if created_task_id is not None:
            async with AsyncSessionMaker() as db:
                await db.execute(delete(AsyncTask).where(AsyncTask.id == created_task_id))
                await db.commit()
        await engine.dispose()
        settings.SQS_QUEUE_URL = original_sqs_url
        app.dependency_overrides.pop(get_idempotency_handler, None)