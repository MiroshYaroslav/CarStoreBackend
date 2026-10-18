from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseDB

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.product_color import ProductColor
    from app.models.product_engine import ProductEngine
    from app.models.product_trim import ProductTrim
    from app.models.review import Review


class Product(BaseDB):
    __tablename__ = "product"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    name: Mapped[str] = mapped_column(String(100))

    description: Mapped[str | None] = mapped_column(Text)

    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), index=True
    )

    image_url: Mapped[str | None] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="products", lazy="raise")

    engines: Mapped[list["ProductEngine"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="raise"
    )

    colors: Mapped[list["ProductColor"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="raise"
    )

    trims: Mapped[list["ProductTrim"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="raise"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="raise"
    )
