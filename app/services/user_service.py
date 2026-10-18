import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.auth_service import AuthService
from app.services.base import BaseService


class UserService(BaseService):
    def __init__(
        self, session: AsyncSession, repo: UserRepository, auth_service: AuthService
    ) -> None:
        super().__init__(session)
        self._repo = repo
        self._auth_service = auth_service

    async def list_users(self, offset: int = 0, limit: int = 100) -> list[UserRead]:
        users = await self._repo.get_many(offset=offset, limit=limit)
        return [UserRead.model_validate(u) for u in users]

    async def get_user(self, user_id: uuid.UUID) -> UserRead:
        user = await self._repo.get(user_id)
        if user is None:
            raise NotFoundException("User not found")
        return UserRead.model_validate(user)

    async def authenticate_user(self, username_or_email: str, password: str) -> User | None:
        user = await self._repo.get_by_email(email=username_or_email)
        if user is None:
            user = await self._repo.get_by_username(username=username_or_email)
        if user is None or not self._auth_service.verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user_id: uuid.UUID) -> str:
        return self._auth_service.create_access_token(user_id)

    async def create_user(self, user_in: UserCreate) -> UserRead:
        if await self._repo.get_by_email(email=user_in.email):
            raise ConflictException("Email already registered")
        if user_in.username and await self._repo.get_by_username(username=user_in.username):
            raise ConflictException("Username already taken")

        user_dict = user_in.model_dump()
        user_dict["password_hash"] = self._auth_service.get_password_hash(user_dict.pop("password"))

        try:
            user = await self._repo.create(data=user_dict)
            await self._session.commit()
            return UserRead.model_validate(user)
        except IntegrityError:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail="DB Error")

    async def update_user(self, user_id: uuid.UUID, user_in: UserUpdate) -> UserRead:
        user = await self._repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = self._auth_service.get_password_hash(
                update_data.pop("password")
            )

        try:
            updated_user = await self._repo.update(pk=user_id, data=update_data)
            if updated_user is None:
                raise NotFoundException("User not found")
            await self._session.commit()
            return UserRead.model_validate(updated_user)
        except IntegrityError:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail="DB Error")

    async def delete_user(self, user_id: uuid.UUID) -> None:
        try:
            deleted = await self._repo.delete(pk=user_id)
            if not deleted:
                raise NotFoundException("User not found")
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail="DB Error")
