import uuid
from decimal import Decimal

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.product_color import ProductColor
from app.models.product_engine import ProductEngine
from app.models.product_trim import ProductTrim
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    _model = Product

    async def get_with_relations(self, product_id: uuid.UUID) -> Product | None:
        query = (
            select(Product)
            .options(
                selectinload(Product.engines),
                selectinload(Product.colors),
                selectinload(Product.trims),
            )
            .where(Product.id == product_id)
        )
        result = await self._require_session().execute(query)
        return result.scalars().first()

    async def get_multi_filtered(
        self,
        category_id: list[uuid.UUID] | None,
        search: str | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        sort: str | None,
        active_only: bool = True,
    ):
        query = select(Product).options(
            selectinload(Product.engines), selectinload(Product.colors), selectinload(Product.trims)
        )

        if active_only:
            query = query.where(Product.is_active == True)

        if category_id:
            query = query.where(Product.category_id.in_(category_id))
        search_term = search.strip() if search else ""
        if search_term:
            # icontains applies a case-insensitive substring match and safely
            # escapes LIKE wildcard characters when autoescape is enabled.
            query = query.where(Product.name.icontains(search_term, autoescape=True))
        if min_price is not None:
            query = query.where(Product.base_price >= min_price)
        if max_price is not None:
            query = query.where(Product.base_price <= max_price)

        if sort == "price-asc":
            query = query.order_by(asc(Product.base_price))
        elif sort == "price-desc":
            query = query.order_by(desc(Product.base_price))
        elif sort in ["power-asc", "power-desc"]:
            max_power_sq = (
                select(func.max(ProductEngine.power))
                .where(ProductEngine.product_id == Product.id)
                .scalar_subquery()
            )
            if sort == "power-asc":
                query = query.order_by(asc(max_power_sq))
            else:
                query = query.order_by(desc(max_power_sq))

        result = await self._require_session().execute(query)
        return result.scalars().unique().all()


class EngineRepository(BaseRepository[ProductEngine]):
    _model = ProductEngine


class ColorRepository(BaseRepository[ProductColor]):
    _model = ProductColor


class TrimRepository(BaseRepository[ProductTrim]):
    _model = ProductTrim
