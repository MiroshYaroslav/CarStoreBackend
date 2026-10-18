import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.api.dependencies import get_user_repository
from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.main import app


def test_access_token_contains_subject_and_configured_expiry():
    user_id = uuid.uuid4()

    payload = decode_access_token(create_access_token(user_id))

    assert payload["sub"] == str(user_id)
    assert payload["exp"] - payload["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_access_token_rejects_modified_signature():
    token = create_access_token(uuid.uuid4())
    header_and_payload, signature = token.rsplit(".", maxsplit=1)
    replacement = "A" if signature[0] != "A" else "B"
    tampered_token = f"{header_and_payload}.{replacement}{signature[1:]}"

    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered_token)


@pytest.mark.asyncio
async def test_expired_token_returns_401_on_authenticated_route():
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    expired_token = jwt.encode(
        {"sub": str(user_id), "iat": now - timedelta(minutes=2), "exp": now - timedelta(minutes=1)},
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    user_repository = SimpleNamespace(get=AsyncMock())
    app.dependency_overrides[get_user_repository] = lambda: user_repository

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {expired_token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    user_repository.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_valid_token_authenticates_user():
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="driver@example.com",
        username="driver",
        first_name="Test",
        last_name="Driver",
        created_at=now,
        updated_at=now,
    )
    user_repository = SimpleNamespace(get=AsyncMock(return_value=user))
    app.dependency_overrides[get_user_repository] = lambda: user_repository

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    user_repository.get.assert_awaited_once_with(user.id)


def test_decode_rejects_expired_token():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        },
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(ExpiredSignatureError):
        decode_access_token(token)
