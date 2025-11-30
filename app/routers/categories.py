from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from app.database import get_db
from app import crud, schemas
from app.models import Category

router = APIRouter(prefix="/categories", tags=["categories"])
logger = logging.getLogger("bmw_api.categories")

@router.get("/", response_model=list[schemas.CategoryRead])
async def read_categories(db: AsyncSession = Depends(get_db)):
    try:
        logger.info("GET /categories/ called")
        return await crud.get_categories(db)
    except Exception:
        logger.exception("Failed to read categories")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=schemas.CategoryRead)
async def create_category(category: schemas.CategoryCreate, db: AsyncSession = Depends(get_db)):
    try:
        logger.info("POST /categories/ called with payload: %s", category.model_dump())
        new_category = Category(**category.model_dump())
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        logger.info("Category created id=%s", new_category.id)
        return new_category
    except Exception:
        logger.exception("Failed to create category")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/{category_id}", response_model=schemas.CategoryRead)
async def update_category(category_id: int, category: schemas.CategoryUpdate, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.get(Category, category_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Category not found")
        data = category.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        return existing
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update category")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{category_id}", response_model=dict)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):

    try:
        category = await db.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        result = await db.execute(
            text("SELECT 1 FROM product WHERE category_id = :cat_id LIMIT 1"),
            {"cat_id": category_id}
        )
        if result.first():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete category because it has associated products"
            )

        await db.delete(category)
        await db.commit()

        return {"status": "ok", "message": f"Category {category_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete category: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
