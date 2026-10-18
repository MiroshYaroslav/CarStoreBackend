import uuid

from sqlalchemy import select

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    _model = Review

    async def get_by_product(self, product_id: uuid.UUID):
        query = (
            select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc())
        )
        result = await self._require_session().execute(query)
        return result.scalars().all()
