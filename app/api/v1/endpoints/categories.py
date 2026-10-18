import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import DBSession
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter()


def get_category_repo(session: DBSession) -> CategoryRepository:
    return CategoryRepository(session)


CategoryRepoDep = Annotated[CategoryRepository, Depends(get_category_repo)]


def get_category_service(session: DBSession, repo: CategoryRepoDep) -> CategoryService:
    return CategoryService(session, repo)


CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]


@router.get("/", response_model=list[CategoryRead])
async def read_categories(service: CategoryServiceDep):
    return await service.list_categories()


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, service: CategoryServiceDep):
    return await service.create_category(category)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID, category: CategoryUpdate, service: CategoryServiceDep
):
    return await service.update_category(category_id, category)


@router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID, service: CategoryServiceDep, hard_delete: bool = False
):
    await service.delete_category(category_id, hard_delete)
    return {
        "status": "ok",
        "message": f"Category {category_id} deleted successfully (hard_delete={hard_delete})",
    }
