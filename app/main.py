from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from typing import List

from app.database import engine, Base, get_db
from app.schemas import Car, UserRegister, UserLogin
from app.crud import cars, favorites, cart, users


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/check-db")
def check_db():
    from app.database import engine
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT NOW()"))
            return {"status": "Database connected", "time": list(result)[0][0]}
    except Exception as e:
        return {"status": "Error", "detail": str(e)}

@app.get("/api/cars", response_model=List[Car])
def get_cars(brand: str = None, search: str = None, sort: str = None, db=Depends(get_db)):
    return cars.get_cars(db, brand, search, sort)

@app.post("/api/cars", response_model=Car)
def add_car(car: Car, db=Depends(get_db)):
    return cars.add_car(db, car)

@app.patch("/api/cars/{car_id}", response_model=Car)
def update_car(car_id: int, car: Car, db=Depends(get_db)):
    return cars.update_car(db, car_id, car)

@app.delete("/api/cars/{car_id}")
def delete_car(car_id: int, db=Depends(get_db)):
    return cars.delete_car(db, car_id)

@app.post("/api/favorites/{user_id}/{car_id}")
def add_favorite(user_id: int, car_id: int, db=Depends(get_db)):
    return favorites.add_favorite(db, user_id, car_id)

@app.delete("/api/favorites/{user_id}/{car_id}")
def remove_favorite(user_id: int, car_id: int, db=Depends(get_db)):
    return favorites.remove_favorite(db, user_id, car_id)

@app.get("/api/favorites/{user_id}", response_model=List[Car])
def get_user_favorites(user_id: int, db=Depends(get_db)):
    return favorites.get_favorites(db, user_id)

@app.delete("/api/favorites/{user_id}")
def clear_user_favorites(user_id: int, db=Depends(get_db)):
    return favorites.clear_favorites(db, user_id)

@app.post("/api/cart/{user_id}/{car_id}")
def add_cart(user_id: int, car_id: int, db=Depends(get_db)):
    return cart.add_cart(db, user_id, car_id)

@app.delete("/api/cart/{user_id}/{car_id}")
def remove_cart(user_id: int, car_id: int, db=Depends(get_db)):
    return cart.remove_cart(db, user_id, car_id)

@app.get("/api/cart/{user_id}", response_model=List[Car])
def get_user_cart(user_id: int, db=Depends(get_db)):
    return cart.get_cart(db, user_id)

@app.delete("/api/cart/{user_id}")
def clear_user_cart(user_id: int, db=Depends(get_db)):
    return cart.clear_cart(db, user_id)

@app.post("/api/register")
def register(user: UserRegister, db=Depends(get_db)):
    return users.register_user(db, user)

@app.post("/api/login")
def login(user: UserLogin, db=Depends(get_db)):
    return users.login_user(db, user)
