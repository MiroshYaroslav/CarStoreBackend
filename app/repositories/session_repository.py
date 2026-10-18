import uuid

from sqlalchemy import select

from app.models.session import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    _model = Session

    async def get_for_update(self, session_id: uuid.UUID) -> Session | None:
        result = await self._require_session().execute(
            select(Session).where(Session.id == session_id).with_for_update()
        )
        return result.scalar_one_or_none()
