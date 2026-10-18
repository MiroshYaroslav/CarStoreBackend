import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, DBSession
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.favorite import FavoriteCreate, FavoriteRead
from app.services.favorite_service import FavoriteService

router = APIRouter()


def get_favorite_repo(session: DBSession) -> FavoriteRepository:
    return FavoriteRepository(session)


def get_product_repo(session: DBSession) -> ProductRepository:
    return ProductRepository(session)


FavoriteRepoDep = Annotated[FavoriteRepository, Depends(get_favorite_repo)]
ProductRepoDep = Annotated[ProductRepository, Depends(get_product_repo)]


def get_favorite_service(
    session: DBSession, repo: FavoriteRepoDep, products: ProductRepoDep
) -> FavoriteService:
    return FavoriteService(session, repo, products)


FavoriteServiceDep = Annotated[FavoriteService, Depends(get_favorite_service)]


@router.get("/", response_model=list[FavoriteRead])
async def get_my_favorites(user: CurrentUser, service: FavoriteServiceDep):
    return await service.list_favorites(user.id)


@router.post("/", response_model=FavoriteRead, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    favorite_in: FavoriteCreate, user: CurrentUser, service: FavoriteServiceDep
):
    return await service.add_favorite(user.id, favorite_in)


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    favorite_id: uuid.UUID, user: CurrentUser, service: FavoriteServiceDep
):
    await service.remove_favorite(user.id, favorite_id)
