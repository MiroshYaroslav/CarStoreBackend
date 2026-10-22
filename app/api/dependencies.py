import uuid
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionMaker
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.token import TokenPayload
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
optional_oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_session_dep() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionMaker() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_session_dep)]


def get_user_repository(session: DBSession) -> UserRepository:
    return UserRepository(session)


def get_auth_service() -> AuthService:
    return AuthService()


async def get_current_user(
    session: DBSession,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
        user_uuid = uuid.UUID(token_data.sub)
    except (InvalidTokenError, ValidationError, ValueError, TypeError):
        raise credentials_exception

    user = await user_repo.get(user_uuid)
    if not user:
        raise credentials_exception
    return user


async def get_optional_user(
    session: DBSession,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token: str | None = Depends(optional_oauth),
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(session, user_repo, token)
    except HTTPException:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]


def is_catalog_admin(user: User) -> bool:
    allowed_user_ids = {
        user_id.strip().casefold()
        for user_id in settings.PRODUCT_IMAGE_UPLOAD_ALLOWED_USER_IDS
        if user_id.strip()
    }
    return str(user.id).casefold() in allowed_user_ids


async def require_catalog_admin(user: CurrentUser) -> User:
    if not is_catalog_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Catalog administrator required"
        )
    return user


CatalogAdmin = Annotated[User, Depends(require_catalog_admin)]
