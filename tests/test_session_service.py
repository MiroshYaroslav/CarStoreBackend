import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.security import decode_access_token
from app.services.auth_service import AuthService
from app.services.session_service import SessionService


@pytest.mark.asyncio
async def test_session_creation_stores_only_a_hash_and_returns_token_pair():
    user_id = uuid.uuid4()
    database_session = SimpleNamespace(commit=AsyncMock())
    session_repository = SimpleNamespace(create=AsyncMock())
    service = SessionService(database_session, session_repository, AuthService())

    access_token, refresh_token = await service.create_session(user_id)

    session_id_raw, secret = refresh_token.split(".", maxsplit=1)
    record = session_repository.create.await_args.args[0]
    assert record["id"] == uuid.UUID(session_id_raw)
    assert record["user_id"] == user_id
    assert record["refresh_token_hash"] != secret
    assert AuthService.verify_refresh_token(secret, record["refresh_token_hash"])
    assert record["expires_at"] > datetime.now(timezone.utc)
    assert decode_access_token(access_token)["sub"] == str(user_id)
    database_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_rotation_replaces_old_session():
    user_id = uuid.uuid4()
    old_session_id = uuid.uuid4()
    old_refresh_token, old_hash = AuthService.create_refresh_token(old_session_id)
    old_record = SimpleNamespace(
        id=old_session_id,
        user_id=user_id,
        refresh_token_hash=old_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    database_session = SimpleNamespace(commit=AsyncMock())
    session_repository = SimpleNamespace(
        get_for_update=AsyncMock(return_value=old_record),
        delete=AsyncMock(return_value=True),
        create=AsyncMock(),
    )
    service = SessionService(database_session, session_repository, AuthService())

    result = await service.rotate_refresh_token(old_refresh_token)

    assert result is not None
    access_token, new_refresh_token = result
    new_session_id_raw, new_secret = new_refresh_token.split(".", maxsplit=1)
    new_record = session_repository.create.await_args.args[0]
    assert uuid.UUID(new_session_id_raw) != old_session_id
    assert new_record["id"] == uuid.UUID(new_session_id_raw)
    assert new_record["user_id"] == user_id
    assert AuthService.verify_refresh_token(new_secret, new_record["refresh_token_hash"])
    assert session_repository.delete.await_args.args == (old_session_id,)
    assert decode_access_token(access_token)["sub"] == str(user_id)
    database_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_expired_refresh_session_is_deleted():
    session_id = uuid.uuid4()
    refresh_token, token_hash = AuthService.create_refresh_token(session_id)
    expired_record = SimpleNamespace(
        id=session_id,
        user_id=uuid.uuid4(),
        refresh_token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    database_session = SimpleNamespace(commit=AsyncMock())
    session_repository = SimpleNamespace(
        get_for_update=AsyncMock(return_value=expired_record),
        delete=AsyncMock(return_value=True),
    )
    service = SessionService(database_session, session_repository, AuthService())

    result = await service.rotate_refresh_token(refresh_token)

    assert result is None
    session_repository.delete.assert_awaited_once_with(session_id)
    database_session.commit.assert_awaited_once()
