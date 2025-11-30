from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/phone-numbers", tags=["phone-numbers"])
logger = logging.getLogger("bmw_api.phone_numbers")


@router.get("/", response_model=list[schemas.PhoneNumberRead])
async def list_phone_numbers(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(models.PhoneNumber))
        return res.scalars().all()
    except Exception:
        logger.exception("Failed to list phone numbers")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=schemas.PhoneNumberRead)
async def create_phone_number(payload: schemas.PhoneNumberCreate, db: AsyncSession = Depends(get_db)):
    try:
        pn = models.PhoneNumber(**payload.model_dump())
        db.add(pn)
        await db.commit()
        await db.refresh(pn)
        return pn
    except Exception:
        logger.exception("Failed to create phone number")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{pn_id}", response_model=schemas.PhoneNumberRead)
async def update_phone_number(pn_id: int, payload: schemas.PhoneNumberUpdate, db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(models.PhoneNumber).where(models.PhoneNumber.id == pn_id))
        pn = res.scalars().first()
        if not pn:
            raise HTTPException(status_code=404, detail="Phone number not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(pn, k, v)
        await db.commit()
        await db.refresh(pn)
        return pn
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update phone number")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{pn_id}", response_model=dict)
async def delete_phone_number(pn_id: int, db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(models.PhoneNumber).where(models.PhoneNumber.id == pn_id))
        pn = res.scalars().first()
        if not pn:
            raise HTTPException(status_code=404, detail="Phone number not found")
        await db.delete(pn)
        await db.commit()
        return {"status": "ok", "message": f"Phone number {pn_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete phone number")
        raise HTTPException(status_code=500, detail="Internal server error")
