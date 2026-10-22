import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import CurrentUser, DBSession
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate
from app.services.review_service import ReviewService

router = APIRouter()


def get_review_repo(session: DBSession) -> ReviewRepository:
    return ReviewRepository(session)


def get_product_repo(session: DBSession) -> ProductRepository:
    return ProductRepository(session)


ReviewRepoDep = Annotated[ReviewRepository, Depends(get_review_repo)]
ProductRepoDep = Annotated[ProductRepository, Depends(get_product_repo)]


def get_review_service(
    session: DBSession, repo: ReviewRepoDep, products: ProductRepoDep
) -> ReviewService:
    return ReviewService(session, repo, products)


ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]


@router.get("/", response_model=list[ReviewRead])
async def get_reviews(service: ReviewServiceDep, product_id: uuid.UUID | None = Query(None)):
    return await service.list_reviews(product_id)


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewCreate, service: ReviewServiceDep, user: CurrentUser):
    return await service.create_review(review, user.id)


@router.patch("/{review_id}", response_model=ReviewRead)
async def update_review(
    review_id: uuid.UUID, review: ReviewUpdate, service: ReviewServiceDep, user: CurrentUser
):
    return await service.update_review(review_id, user.id, review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: uuid.UUID, service: ReviewServiceDep, user: CurrentUser):
    await service.delete_review(review_id, user.id)
