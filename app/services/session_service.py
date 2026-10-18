import uuid
from datetime import datetime, timedelta, timezone

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.session_repository import SessionRepository
from app.services.auth_service import AuthService
from app.services.base import BaseService


class SessionService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        sessions: SessionRepository,
        auth_service: AuthService,
    ) -> None:
        super().__init__(session)
        self._sessions = sessions
        self._auth_service = auth_service

    @staticmethod
    def _parse_refresh_token(token: str) -> tuple[uuid.UUID, str] | None:
        session_id_raw, separator, secret = token.partition(".")
        if not separator or not secret:
            return None
        try:
            return uuid.UUID(session_id_raw), secret
        except ValueError:
            return None

    async def _new_refresh_token(self, session_id: uuid.UUID) -> tuple[str, str]:
        return await run_in_threadpool(self._auth_service.create_refresh_token, session_id)

    async def _matches_hash(self, secret: str, token_hash: str) -> bool:
        return await run_in_threadpool(self._auth_service.verify_refresh_token, secret, token_hash)

    async def create_session(self, user_id: uuid.UUID) -> tuple[str, str]:
        session_id = uuid.uuid4()
        refresh_token, token_hash = await self._new_refresh_token(session_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self._sessions.create(
            {
                "id": session_id,
                "user_id": user_id,
                "refresh_token_hash": token_hash,
                "expires_at": expires_at,
            }
        )
        await self._session.commit()
        return self._auth_service.create_access_token(user_id), refresh_token

    async def rotate_refresh_token(self, token: str) -> tuple[str, str] | None:
        parsed = self._parse_refresh_token(token)
        if parsed is None:
            return None

        session_id, secret = parsed
        session_record = await self._sessions.get_for_update(session_id)
        if session_record is None:
            return None

        if session_record.expires_at <= datetime.now(timezone.utc):
            await self._sessions.delete(session_id)
            await self._session.commit()
            return None

        if not await self._matches_hash(secret, session_record.refresh_token_hash):
            return None

        user_id = session_record.user_id
        await self._sessions.delete(session_id)

        new_session_id = uuid.uuid4()
        new_refresh_token, token_hash = await self._new_refresh_token(new_session_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._sessions.create(
            {
                "id": new_session_id,
                "user_id": user_id,
                "refresh_token_hash": token_hash,
                "expires_at": expires_at,
            }
        )
        await self._session.commit()
        return self._auth_service.create_access_token(user_id), new_refresh_token

    async def revoke_refresh_token(self, token: str | None) -> None:
        if not token:
            return

        parsed = self._parse_refresh_token(token)
        if parsed is None:
            return

        session_id, secret = parsed
        session_record = await self._sessions.get_for_update(session_id)
        if session_record is None:
            return

        if await self._matches_hash(secret, session_record.refresh_token_hash):
            await self._sessions.delete(session_id)
            await self._session.commit()
