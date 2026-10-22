import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.dependencies import is_catalog_admin, require_catalog_admin
from app.exceptions.base import NotFoundException
from app.schemas.review import ReviewUpdate
from app.services.cart_service import CartService
from app.services.review_service import ReviewService


def test_catalog_admin_is_selected_by_configured_user_id(monkeypatch):
    allowed_user_id = uuid.uuid4()
    monkeypatch.setattr(
        "app.api.dependencies.settings.PRODUCT_IMAGE_UPLOAD_ALLOWED_USER_IDS",
        [str(allowed_user_id)],
    )

    assert is_catalog_admin(SimpleNamespace(id=allowed_user_id))
    assert not is_catalog_admin(SimpleNamespace(id=uuid.uuid4()))


@pytest.mark.asyncio
async def test_catalog_admin_dependency_rejects_other_users():
    with pytest.raises(HTTPException) as exc_info:
        await require_catalog_admin(SimpleNamespace(id=uuid.uuid4()))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cart_item_cannot_be_removed_without_owner_match():
    item_id = uuid.uuid4()
    user_id = uuid.uuid4()
    repository = SimpleNamespace(get_owned_item=AsyncMock(return_value=None), delete=AsyncMock())
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    service = CartService(session, repository, SimpleNamespace())

    with pytest.raises(NotFoundException):
        await service.remove_item(item_id, user_id=user_id)

    repository.get_owned_item.assert_awaited_once_with(item_id, user_id, None)
    repository.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_cart_removal_requires_user_or_guest_session():
    repository = SimpleNamespace(get_owned_item=AsyncMock(), delete=AsyncMock())
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    service = CartService(session, repository, SimpleNamespace())

    with pytest.raises(HTTPException) as exc_info:
        await service.remove_item(uuid.uuid4())

    assert exc_info.value.status_code == 400
    repository.get_owned_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_review_cannot_be_updated_or_deleted_by_non_owner():
    review_id = uuid.uuid4()
    user_id = uuid.uuid4()
    repository = SimpleNamespace(
        get_owned_review=AsyncMock(return_value=None),
        update=AsyncMock(),
        delete=AsyncMock(),
    )
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    service = ReviewService(session, repository, SimpleNamespace())

    with pytest.raises(NotFoundException):
        await service.update_review(review_id, user_id, ReviewUpdate(rating=5))
    with pytest.raises(NotFoundException):
        await service.delete_review(review_id, user_id)

    assert repository.get_owned_review.await_count == 2
    repository.update.assert_not_awaited()
    repository.delete.assert_not_awaited()
