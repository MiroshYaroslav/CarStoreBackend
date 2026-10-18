from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    _model = User

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(self._model).where(self._model.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(self._model).where(self._model.username == username)
        )
        return result.scalar_one_or_none()
