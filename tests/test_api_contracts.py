import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints import auth as auth_endpoints
from app.api.v1.endpoints.auth import get_session_service, get_user_service
from app.api.v1.endpoints.products import get_product_service, get_s3_service
from app.main import app


@pytest.fixture
def user():
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="driver@example.com",
        username="driver",
        first_name="Test",
        last_name="Driver",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def product():
    now = datetime.now(timezone.utc)
    return {
        "id": uuid.uuid4(),
        "name": "BMW Test",
        "description": None,
        "base_price": "50000.00",
        "category_id": None,
        "image_url": "https://images.example.com/bmw.jpg",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "engines": [],
        "colors": [],
        "trims": [],
    }


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_returns_token_and_nested_user(client, user, monkeypatch):
    monkeypatch.setattr(auth_endpoints, "is_secure", False)
    service = SimpleNamespace(
        authenticate_user=AsyncMock(return_value=user),
        create_access_token=lambda user_id: "test.jwt.token",
    )
    session_service = SimpleNamespace(
        create_session=AsyncMock(return_value=("test.jwt.token", "session-id.refresh-secret"))
    )
    app.dependency_overrides[get_user_service] = lambda: service
    app.dependency_overrides[get_session_service] = lambda: session_service

    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "driver", "password": "secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "test.jwt.token"
    assert body["token_type"] == "bearer"
    assert body["user"]["id"] == str(user.id)
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "; secure" not in set_cookie
    assert "samesite=lax" in set_cookie
    session_service.create_session.assert_awaited_once_with(user.id)


def test_refresh_cookie_is_secure_when_environment_is_production(monkeypatch):
    monkeypatch.setattr(auth_endpoints, "is_secure", True)
    set_response = auth_endpoints.Response()
    clear_response = auth_endpoints.Response()

    auth_endpoints.set_refresh_cookie(set_response, "test-refresh-token")
    auth_endpoints.clear_refresh_cookie(clear_response)

    assert "; secure" in set_response.headers["set-cookie"].lower()
    assert "; secure" in clear_response.headers["set-cookie"].lower()


@pytest.mark.asyncio
async def test_refresh_rotates_cookie_and_returns_access_token(client):
    session_service = SimpleNamespace(
        rotate_refresh_token=AsyncMock(
            return_value=("refreshed.jwt.token", "new-session.refresh-secret")
        )
    )
    app.dependency_overrides[get_session_service] = lambda: session_service

    client.cookies.set("refresh_token", "old-session.refresh-secret")
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "refreshed.jwt.token",
        "token_type": "bearer",
    }
    assert "new-session.refresh-secret" in response.headers["set-cookie"]
    session_service.rotate_refresh_token.assert_awaited_once_with("old-session.refresh-secret")


@pytest.mark.asyncio
async def test_invalid_refresh_returns_401_and_clears_cookie(client):
    session_service = SimpleNamespace(rotate_refresh_token=AsyncMock(return_value=None))
    app.dependency_overrides[get_session_service] = lambda: session_service

    client.cookies.set("refresh_token", "invalid-token")
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert "max-age=0" in response.headers["set-cookie"].lower()


@pytest.mark.asyncio
async def test_logout_revokes_session_and_clears_cookie(client):
    session_service = SimpleNamespace(revoke_refresh_token=AsyncMock())
    app.dependency_overrides[get_session_service] = lambda: session_service

    client.cookies.set("refresh_token", "session-id.refresh-secret")
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert "max-age=0" in response.headers["set-cookie"].lower()
    session_service.revoke_refresh_token.assert_awaited_once_with("session-id.refresh-secret")


@pytest.mark.asyncio
async def test_list_products_returns_product_payload(client, product):
    service = SimpleNamespace(list_products=AsyncMock(return_value=[product]))
    app.dependency_overrides[get_product_service] = lambda: service

    response = await client.get("/api/v1/products/", params={"search": "BMW"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(product["id"])
    assert response.json()[0]["image_url"] == product["image_url"]
    service.list_products.assert_awaited_once()


@pytest.mark.asyncio
async def test_product_image_upload_persists_s3_url(client, product):
    image_url = "https://catalog.s3.eu-central-1.amazonaws.com/products/test.jpg"
    service = SimpleNamespace(
        update_product_image=AsyncMock(return_value={**product, "image_url": image_url})
    )
    s3_service = SimpleNamespace(upload_image=AsyncMock(return_value=image_url))
    app.dependency_overrides[get_product_service] = lambda: service
    app.dependency_overrides[get_s3_service] = lambda: s3_service

    response = await client.post(
        f"/api/v1/products/{product['id']}/image",
        files={"file": ("bmw.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == image_url
    service.update_product_image.assert_awaited_once_with(product["id"], image_url)
