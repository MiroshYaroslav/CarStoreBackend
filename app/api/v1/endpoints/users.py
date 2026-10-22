import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    CatalogAdmin,
    CurrentUser,
    DBSession,
    get_auth_service,
    get_user_repository,
    is_catalog_admin,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()

UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(
    session: DBSession, repo: UserRepoDep, auth_service: AuthServiceDep
) -> UserService:
    return UserService(session, repo, auth_service)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/", response_model=list[UserRead])
async def list_users(
    service: UserServiceDep,
    _: CatalogAdmin,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[UserRead]:
    return await service.list_users(offset=offset, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, service: UserServiceDep, current_user: CurrentUser):
    if current_user.id != user_id and not is_catalog_admin(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID, payload: UserUpdate, service: UserServiceDep, current_user: CurrentUser
):
    if current_user.id != user_id and not is_catalog_admin(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await service.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, service: UserServiceDep, current_user: CurrentUser):
    if current_user.id != user_id and not is_catalog_admin(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await service.delete_user(user_id)
