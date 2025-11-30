from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import logging
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = logging.getLogger("bmw_api.reviews")

@router.post("/", response_model=schemas.ReviewRead)
async def create_review(review: schemas.ReviewCreate, db: AsyncSession = Depends(get_db)):
    try:
        logger.info("POST /reviews/ called with payload: %s", review.model_dump())
        payload = review.model_dump()

        rating = payload.get("rating")
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="rating must be integer between 1 and 5")

        res = await db.execute(select(models.Product).where(models.Product.id == payload["product_id"]))
        product = res.scalars().first()
        if not product:
            raise HTTPException(status_code=400, detail="product_id not found")

        new_review = models.Review(**payload)
        db.add(new_review)
        try:
            await db.commit()
            await db.refresh(new_review)
        except IntegrityError as e:
            await db.rollback()
            logger.exception("DB IntegrityError while creating review")
            raise HTTPException(status_code=400, detail="Database integrity error") from e

        logger.info("Review created id=%s", new_review.id)
        return new_review
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create review")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[schemas.ReviewRead])
async def get_reviews(
    product_id: int | None = Query(None, description="Filter reviews by product_id"),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info("GET /reviews/ called, product_id=%s", product_id)
        if product_id is not None:
            query = select(models.Review).where(models.Review.product_id == product_id)
        else:
            query = select(models.Review).where(models.Review.product_id.isnot(None))

        result = await db.execute(query)
        reviews = result.scalars().all()
        return reviews
    except Exception:
        logger.exception("Failed to fetch reviews")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{review_id}", response_model=schemas.ReviewRead)
async def update_review(review_id: int, update: schemas.ReviewUpdate, db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(models.Review).where(models.Review.id == review_id))
        review = res.scalars().first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        data = update.model_dump(exclude_unset=True)
        # Validate rating if provided
        if "rating" in data:
            rating = data["rating"]
            if rating is not None and not (1 <= int(rating) <= 5):
                raise HTTPException(status_code=400, detail="rating must be integer between 1 and 5")
        for k, v in data.items():
            setattr(review, k, v)
        await db.commit()
        await db.refresh(review)
        return review
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update review")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{review_id}", response_model=dict)
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(models.Review).where(models.Review.id == review_id))
        review = res.scalars().first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        await db.delete(review)
        await db.commit()
        return {"status": "ok", "message": f"Review {review_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete review")
        raise HTTPException(status_code=500, detail="Internal server error")
