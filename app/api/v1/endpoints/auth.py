from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentUser, DBSession, get_auth_service, get_user_repository
from app.core.config import settings
from app.exceptions.base import UnauthorizedException
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.token import AccessToken, Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.services.user_service import UserService

router = APIRouter()
is_secure = settings.ENVIRONMENT == "production"


def get_user_service(
    session: DBSession,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserService:
    return UserService(session, repository, auth_service)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
REFRESH_COOKIE_NAME = "refresh_token"


def get_session_repository(session: DBSession) -> SessionRepository:
    return SessionRepository(session)


def get_session_service(
    session: DBSession,
    repository: Annotated[SessionRepository, Depends(get_session_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SessionService:
    return SessionService(session, repository, auth_service)


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, service: UserServiceDep):
    return await service.create_user(user_in)


@router.post("/token", response_model=Token)
async def login_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserServiceDep,
    session_service: SessionServiceDep,
):
    user = await service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise UnauthorizedException("Incorrect username or password")

    access_token, refresh_token = await session_service.create_session(user.id)
    set_refresh_cookie(response, refresh_token)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=AccessToken)
async def refresh_access_token(
    response: Response,
    session_service: SessionServiceDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
):
    tokens = await session_service.rotate_refresh_token(refresh_token) if refresh_token else None
    if tokens is None:
        unauthorized_response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired refresh token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
        clear_refresh_cookie(unauthorized_response)
        return unauthorized_response

    access_token, new_refresh_token = tokens
    set_refresh_cookie(response, new_refresh_token)
    return AccessToken(access_token=access_token)


@router.post("/logout")
async def logout(
    response: Response,
    session_service: SessionServiceDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
):
    await session_service.revoke_refresh_token(refresh_token)
    clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: CurrentUser):
    return UserRead.model_validate(current_user)
