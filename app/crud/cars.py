from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import CarDB
from app.schemas import Car
from sqlalchemy import asc, desc, or_, cast, String

def get_cars(db: Session, brand: str = None, search: str = None, sort: str = None):
    query = db.query(CarDB)

    if brand:
        # нечутливий до регістру фільтр
        query = query.filter(CarDB.brand.ilike(f"%{brand}%"))

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                CarDB.brand.ilike(pattern),
                CarDB.color.ilike(pattern),
                cast(CarDB.year, String).ilike(pattern),
                cast(CarDB.power, String).ilike(pattern),
                cast(CarDB.price, String).ilike(pattern)
            )
        )

    if sort:
        if sort == "price-asc": query = query.order_by(asc(CarDB.price))
        elif sort == "price-desc": query = query.order_by(desc(CarDB.price))
        elif sort == "year-asc": query = query.order_by(asc(CarDB.year))
        elif sort == "year-desc": query = query.order_by(desc(CarDB.year))
        elif sort == "power-asc": query = query.order_by(asc(CarDB.power))
        elif sort == "power-desc": query = query.order_by(desc(CarDB.power))
    else:
        query = query.order_by(asc(CarDB.id))

    return query.all()

def add_car(db: Session, car: Car):
    new_car = CarDB(**car.model_dump())
    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return new_car

def update_car(db: Session, car_id: int, car: Car):
    db_car = db.query(CarDB).filter(CarDB.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
    for key, value in car.model_dump(exclude_unset=True).items():
        setattr(db_car, key, value)
    db.commit()
    db.refresh(db_car)
    return db_car

def delete_car(db: Session, car_id: int):
    db_car = db.query(CarDB).filter(CarDB.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
    db.delete(db_car)
    db.commit()
    return {"detail": "Car deleted"}
