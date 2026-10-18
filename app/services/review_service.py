import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.base import BaseService


class ReviewService(BaseService):
    def __init__(
        self, session: AsyncSession, repository: ReviewRepository, products: ProductRepository
    ):
        super().__init__(session)
        self._repository, self._products = repository, products

    async def list_reviews(self, product_id: uuid.UUID | None = None):
        return (
            await self._repository.get_by_product(product_id)
            if product_id
            else await self._repository.get_many()
        )

    async def create_review(self, review_in: ReviewCreate):
        if not await self._products.get_with_relations(review_in.product_id):
            raise NotFoundException("Product not found")
        try:
            result = await self._repository.create(review_in.model_dump())
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Review conflicts with existing data")

    async def update_review(self, review_id: uuid.UUID, update_in: ReviewUpdate):
        try:
            result = await self._repository.update(
                review_id, update_in.model_dump(exclude_unset=True)
            )
            if not result:
                raise NotFoundException("Review not found")
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Review conflicts with existing data")

    async def delete_review(self, review_id: uuid.UUID):
        try:
            if not await self._repository.delete(review_id):
                raise NotFoundException("Review not found")
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
