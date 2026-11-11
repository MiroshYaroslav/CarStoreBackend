"""Idempotently seed an explicitly labelled demo catalog in dev environments.

Run as a one-off ECS task after deploying the image. All prices and vehicle
specifications below are illustrative lab data, not current offers.
"""

import asyncio
import uuid
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func

from app.core.config import settings
from app.core.database import AsyncSessionMaker, engine
from app.models.category import Category
from app.models.product import Product
from app.models.product_color import ProductColor
from app.models.product_engine import ProductEngine
from app.models.product_trim import ProductTrim


_NAMESPACE = uuid.UUID("ca8fba8b-c5d8-4f3d-8d90-96ee61fddbc4")


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, key)


_CATEGORIES = [
    {"key": "sedan", "name": "Sedan (lab demo)", "description": "Illustrative sedan catalog entries for load testing."},
    {"key": "suv", "name": "SUV (lab demo)", "description": "Illustrative SUV catalog entries for load testing."},
    {"key": "electric", "name": "Electric (lab demo)", "description": "Illustrative electric catalog entries for load testing."},
    {"key": "m-performance", "name": "M Performance (lab demo)", "description": "Illustrative BMW M catalog entries for load testing."},
]

_PRODUCTS = [
    ("3-series", "BMW 3 Series (lab demo)", "sedan", "48000.00", "Illustrative catalog record for BMW 3 Series."),
    ("5-series", "BMW 5 Series (lab demo)", "sedan", "62000.00", "Illustrative catalog record for BMW 5 Series."),
    ("7-series", "BMW 7 Series (lab demo)", "sedan", "105000.00", "Illustrative catalog record for BMW 7 Series."),
    ("z4", "BMW Z4 (lab demo)", "sedan", "59000.00", "Illustrative catalog record for BMW Z4."),
    ("x1", "BMW X1 (lab demo)", "suv", "43000.00", "Illustrative catalog record for BMW X1."),
    ("x3", "BMW X3 (lab demo)", "suv", "57000.00", "Illustrative catalog record for BMW X3."),
    ("x5", "BMW X5 (lab demo)", "suv", "79000.00", "Illustrative catalog record for BMW X5."),
    ("x7", "BMW X7 (lab demo)", "suv", "108000.00", "Illustrative catalog record for BMW X7."),
    ("i4", "BMW i4 (lab demo)", "electric", "61000.00", "Illustrative catalog record for BMW i4."),
    ("i5", "BMW i5 (lab demo)", "electric", "72000.00", "Illustrative catalog record for BMW i5."),
    ("ix1", "BMW iX1 (lab demo)", "electric", "52000.00", "Illustrative catalog record for BMW iX1."),
    ("ix", "BMW iX (lab demo)", "electric", "89000.00", "Illustrative catalog record for BMW iX."),
    ("m3", "BMW M3 (lab demo)", "m-performance", "95000.00", "Illustrative catalog record for BMW M3."),
    ("m4", "BMW M4 (lab demo)", "m-performance", "99000.00", "Illustrative catalog record for BMW M4."),
    ("m8", "BMW M8 (lab demo)", "m-performance", "145000.00", "Illustrative catalog record for BMW M8."),
    ("x6-m", "BMW X6 M (lab demo)", "m-performance", "138000.00", "Illustrative catalog record for BMW X6 M."),
]

_ENGINE_SPECS = {
    "sedan": ("Demo petrol", "2.0", 190, "7.5", 235, "Petrol"),
    "suv": ("Demo petrol", "2.0", 210, "7.8", 225, "Petrol"),
    "electric": ("Demo electric motor", "0.0", 250, "5.8", 200, "Electric"),
    "m-performance": ("Illustrative M petrol engine", "3.0", 510, "4.2", 290, "Petrol"),
}


async def _upsert_rows(session, model, rows: list[dict]) -> None:
    statement = insert(model).values(rows)
    values = {
        column.name: getattr(statement.excluded, column.name)
        for column in model.__table__.columns
        if column.name not in {"id", "created_at", "updated_at"}
        and column.name in rows[0]
    }
    values["updated_at"] = func.now()
    await session.execute(
        statement.on_conflict_do_update(index_elements=[model.id], set_=values)
    )


async def seed_catalog() -> dict[str, int]:
    if settings.ENVIRONMENT.casefold() not in {"dev", "development", "test", "staging"}:
        raise RuntimeError("Demo catalog seeding is restricted to non-production environments.")

    category_ids = {entry["key"]: _id(f"category:{entry['key']}") for entry in _CATEGORIES}
    category_rows = [
        {"id": category_ids[entry["key"]], "name": entry["name"], "description": entry["description"], "is_active": True}
        for entry in _CATEGORIES
    ]

    product_rows = []
    engine_rows = []
    color_rows = []
    trim_rows = []
    for key, name, category_key, price, description in _PRODUCTS:
        product_id = _id(f"product:{key}")
        product_rows.append(
            {
                "id": product_id,
                "name": name,
                "description": f"{description} Prices and specifications are fictional lab examples.",
                "base_price": Decimal(price),
                "category_id": category_ids[category_key],
                "image_url": None,
                "is_active": True,
            }
        )
        engine_name, volume, power, acceleration, top_speed, fuel_type = _ENGINE_SPECS[category_key]
        engine_rows.append(
            {
                "id": _id(f"engine:{key}"),
                "product_id": product_id,
                "name": engine_name,
                "volume": Decimal(volume),
                "power": power,
                "acceleration": Decimal(acceleration),
                "top_speed": top_speed,
                "price_modifier": Decimal("0.00"),
                "fuel_type": fuel_type,
            }
        )
        color_rows.append(
            {
                "id": _id(f"color:{key}"),
                "product_id": product_id,
                "name": "Demo Alpine White",
                "hex_code": "#F2F2F2",
                "price_modifier": Decimal("0.00"),
                "image_url": None,
            }
        )
        trim_rows.append(
            {
                "id": _id(f"trim:{key}"),
                "product_id": product_id,
                "name": "Lab demo trim",
                "description": "Illustrative trim option for load testing.",
                "price_modifier": Decimal("2500.00"),
            }
        )

    async with AsyncSessionMaker() as session:
        async with session.begin():
            for model, rows in (
                (Category, category_rows),
                (Product, product_rows),
                (ProductEngine, engine_rows),
                (ProductColor, color_rows),
                (ProductTrim, trim_rows),
            ):
                await _upsert_rows(session, model, rows)

    return {
        "categories": len(category_rows),
        "products": len(product_rows),
        "engines": len(engine_rows),
        "colors": len(color_rows),
        "trims": len(trim_rows),
    }


async def main() -> None:
    try:
        counts = await seed_catalog()
        print(f"Demo catalog seed completed: {counts}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
