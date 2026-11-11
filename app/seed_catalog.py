"""Idempotently seed representative BMW catalog data in non-production environments.

Run as a one-off ECS task after deploying the image. Specifications represent
common model variants; availability and figures vary by market and model year.
Prices are indicative catalog values in EUR because the schema has no currency
column; they are not live offers.
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
    {"key": "sedan", "name": "Sedan", "description": "BMW sedans and coupes."},
    {"key": "suv", "name": "SUV", "description": "BMW Sports Activity Vehicles."},
    {"key": "electric", "name": "Electric", "description": "BMW battery-electric models."},
    {"key": "m-performance", "name": "BMW M", "description": "BMW M high-performance models."},
]

# Base prices and option modifiers are indicative EUR catalog values. The DB
# schema currently stores no currency, torque, or transmission attributes.
_PRODUCTS = [
    ("3-series", "BMW 3 Series", "sedan", "48000.00", "Sport sedan with petrol, diesel and plug-in hybrid powertrains."),
    ("5-series", "BMW 5 Series", "sedan", "62000.00", "Executive sedan offered with petrol, diesel and plug-in hybrid powertrains."),
    ("7-series", "BMW 7 Series", "sedan", "105000.00", "Flagship luxury sedan with electrified petrol and diesel variants."),
    ("z4", "BMW Z4 Roadster", "sedan", "59000.00", "Two-seat roadster with rear-wheel drive and turbocharged petrol engines."),
    ("x1", "BMW X1", "suv", "43000.00", "Compact Sports Activity Vehicle with petrol, diesel and plug-in hybrid variants."),
    ("x3", "BMW X3", "suv", "57000.00", "Mid-size Sports Activity Vehicle with petrol, diesel and plug-in hybrid variants."),
    ("x5", "BMW X5", "suv", "79000.00", "Large Sports Activity Vehicle with petrol, diesel and plug-in hybrid variants."),
    ("x7", "BMW X7", "suv", "108000.00", "Full-size luxury Sports Activity Vehicle with six- and eight-cylinder engines."),
    ("i4", "BMW i4", "electric", "61000.00", "All-electric Gran Coupe with single- and dual-motor configurations."),
    ("i5", "BMW i5", "electric", "72000.00", "All-electric executive sedan with eDrive and dual-motor M variants."),
    ("ix1", "BMW iX1", "electric", "52000.00", "Compact all-electric Sports Activity Vehicle with eDrive and xDrive variants."),
    ("ix", "BMW iX", "electric", "89000.00", "Large all-electric Sports Activity Vehicle with dual-motor xDrive variants."),
    ("m3", "BMW M3 Sedan", "m-performance", "95000.00", "High-performance sports sedan powered by a 3.0-litre M TwinPower Turbo inline-six."),
    ("m4", "BMW M4 Coupe", "m-performance", "99000.00", "High-performance coupe powered by a 3.0-litre M TwinPower Turbo inline-six."),
    ("m8", "BMW M8 Competition Coupe", "m-performance", "145000.00", "Luxury high-performance coupe with a 4.4-litre M TwinPower Turbo V8."),
    ("x6-m", "BMW X6 M Competition", "m-performance", "138000.00", "High-performance Sports Activity Coupe with a 4.4-litre M TwinPower Turbo V8."),
]

# Each tuple is: name, displacement in litres, hp, 0-100 km/h seconds,
# top speed km/h, fuel type, price modifier in EUR. Variant names capture
# drivetrain/grade where that distinction is useful to the catalog.
_ENGINES = {
    "3-series": [
        ("318i sDrive 2.0 petrol", "2.0", 156, "8.6", 218, "Petrol", "0"),
        ("320d sDrive 2.0 diesel", "2.0", 190, "6.9",  235, "Diesel", "2500"),
        ("330e plug-in hybrid", "2.0", 292, "5.9", 230, "Plug-in hybrid", "9000"),
    ],
    "5-series": [
        ("520i sDrive 2.0 petrol", "2.0", 208, "7.5", 230, "Petrol", "0"),
        ("520d sDrive 2.0 diesel", "2.0", 197, "7.3", 233, "Diesel", "1800"),
        ("530e plug-in hybrid", "2.0", 299, "6.3", 230, "Plug-in hybrid", "8500"),
    ],
    "7-series": [
        ("740i xDrive 3.0 petrol mild hybrid", "3.0", 381, "5.4", 250, "Petrol mild hybrid", "0"),
        ("750e xDrive plug-in hybrid", "3.0", 489, "4.8", 250, "Plug-in hybrid", "12000"),
        ("760i xDrive 4.4 V8", "4.4", 544, "4.2", 250, "Petrol", "22000"),
    ],
    "z4": [
        ("sDrive20i 2.0 petrol", "2.0", 197, "6.6", 240, "Petrol", "0"),
        ("sDrive30i 2.0 petrol", "2.0", 258, "5.4", 250, "Petrol", "7000"),
        ("M40i 3.0 petrol", "3.0", 340, "4.5", 250, "Petrol", "14000"),
    ],
    "x1": [
        ("sDrive18i 1.5 petrol", "1.5", 136, "9.2", 208, "Petrol", "0"),
        ("sDrive18d 2.0 diesel", "2.0", 150, "8.9", 210, "Diesel", "1800"),
        ("xDrive25e plug-in hybrid", "1.5", 245, "6.8", 190, "Plug-in hybrid", "7500"),
    ],
    "x3": [
        ("20 xDrive 2.0 petrol mild hybrid", "2.0", 208, "7.8", 215, "Petrol mild hybrid", "0"),
        ("20d xDrive 2.0 diesel mild hybrid", "2.0", 197, "7.7", 215, "Diesel mild hybrid", "2200"),
        ("30e xDrive plug-in hybrid", "2.0", 299, "6.2", 215, "Plug-in hybrid", "9500"),
    ],
    "x5": [
        ("xDrive30d 3.0 diesel mild hybrid", "3.0", 298, "6.1", 233, "Diesel mild hybrid", "0"),
        ("xDrive40i 3.0 petrol mild hybrid", "3.0", 381, "5.4", 250, "Petrol mild hybrid", "5000"),
        ("xDrive50e plug-in hybrid", "3.0", 489, "4.8", 250, "Plug-in hybrid", "11500"),
    ],
    "x7": [
        ("xDrive40i 3.0 petrol mild hybrid", "3.0", 381, "5.8", 250, "Petrol mild hybrid", "0"),
        ("xDrive40d 3.0 diesel mild hybrid", "3.0", 352, "5.9", 245, "Diesel mild hybrid", "2500"),
        ("M60i xDrive 4.4 V8 mild hybrid", "4.4", 530, "4.7", 250, "Petrol mild hybrid", "18000"),
    ],
    "i4": [
        ("eDrive35 rear motor", "0.0", 286, "6.0", 190, "Electric", "0"),
        ("eDrive40 rear motor", "0.0", 340, "5.6", 190, "Electric", "8000"),
        ("M50 xDrive dual motor", "0.0", 544, "3.9", 225, "Electric", "18000"),
    ],
    "i5": [
        ("eDrive40 rear motor", "0.0", 340, "6.0", 193, "Electric", "0"),
        ("xDrive40 dual motor", "0.0", 394, "5.4", 215, "Electric", "7000"),
        ("M60 xDrive dual motor", "0.0", 601, "3.8", 230, "Electric", "18000"),
    ],
    "ix1": [
        ("eDrive20 front motor", "0.0", 204, "8.6", 170, "Electric", "0"),
        ("xDrive30 dual motor", "0.0", 313, "5.6", 180, "Electric", "8500"),
    ],
    "ix": [
        ("xDrive45 dual motor", "0.0", 408, "5.1", 200, "Electric", "0"),
        ("xDrive60 dual motor", "0.0", 544, "4.6", 200, "Electric", "14000"),
        ("M70 xDrive dual motor", "0.0", 659, "3.8", 250, "Electric", "28000"),
    ],
    "m3": [
        ("M3 3.0 inline-six, 6-speed manual, RWD", "3.0", 480, "4.2", 250, "Petrol", "0"),
        ("M3 Competition 3.0 inline-six, RWD", "3.0", 510, "3.9", 250, "Petrol", "7000"),
        ("M3 Competition 3.0 inline-six, M xDrive", "3.0", 530, "3.5", 250, "Petrol", "12000"),
    ],
    "m4": [
        ("M4 3.0 inline-six, 6-speed manual, RWD", "3.0", 480, "4.2", 250, "Petrol", "0"),
        ("M4 Competition 3.0 inline-six, RWD", "3.0", 510, "3.9", 250, "Petrol", "7000"),
        ("M4 Competition 3.0 inline-six, M xDrive", "3.0", 530, "3.5", 250, "Petrol", "12000"),
    ],
    "m8": [
        ("M8 4.4 V8 M TwinPower Turbo", "4.4", 600, "3.3", 250, "Petrol", "0"),
        ("M8 Competition 4.4 V8 M TwinPower Turbo", "4.4", 625, "3.2", 250, "Petrol", "12000"),
    ],
    "x6-m": [
        ("X6 M Competition 4.4 V8 M TwinPower Turbo", "4.4", 625, "3.9", 250, "Petrol mild hybrid", "0"),
    ],
}

_COLORS = [
    ("Alpine White", "#F2F2F2", "0"),
    ("Black Sapphire Metallic", "#101114", "1100"),
    ("Brooklyn Grey Metallic", "#777B80", "1100"),
    ("Portimao Blue Metallic", "#145A9E", "1100"),
    ("Skyscraper Grey Metallic", "#8B8D8F", "1300"),
]

_TRIMS = [
    ("Sport Line", "Sport-focused exterior and interior details.", "0"),
    ("M Sport", "M aerodynamic styling, sport seats and model-specific M details.", "4200"),
    ("M Sport Pro", "M Sport equipment with additional dark exterior and braking details.", "6800"),
]


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
        raise RuntimeError("Catalog seeding is restricted to non-production environments.")

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
                "description": f"{description} Representative specifications; availability varies by market and model year. Base prices are indicative EUR values.",
                "base_price": Decimal(price),
                "category_id": category_ids[category_key],
                "image_url": None,
                "is_active": True,
            }
        )
        for index, (engine_name, volume, power, acceleration, top_speed, fuel_type, modifier) in enumerate(_ENGINES[key]):
            engine_rows.append(
                {
                    "id": _id(f"engine:{key}" if index == 0 else f"engine:{key}:{index}"),
                    "product_id": product_id,
                    "name": engine_name,
                    "volume": Decimal(volume),
                    "power": power,
                    "acceleration": Decimal(acceleration),
                    "top_speed": top_speed,
                    "price_modifier": Decimal(modifier),
                    "fuel_type": fuel_type,
                }
            )
        for index, (color_name, hex_code, modifier) in enumerate(_COLORS):
            color_rows.append(
                {
                    "id": _id(f"color:{key}" if index == 0 else f"color:{key}:{index}"),
                    "product_id": product_id,
                    "name": color_name,
                    "hex_code": hex_code,
                    "price_modifier": Decimal(modifier),
                    "image_url": None,
                }
            )
        for index, (trim_name, trim_description, modifier) in enumerate(_TRIMS):
            trim_rows.append(
                {
                    "id": _id(f"trim:{key}" if index == 0 else f"trim:{key}:{index}"),
                    "product_id": product_id,
                    "name": trim_name,
                    "description": trim_description,
                    "price_modifier": Decimal(modifier),
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
        print(f"Catalog seed completed: {counts}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
