from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseDB

if TYPE_CHECKING:
    from app.models.product import Product


class ProductEngine(BaseDB):
    __tablename__ = "product_engine"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(100))

    volume: Mapped[Decimal] = mapped_column(Numeric(3, 1))

    power: Mapped[int] = mapped_column(Integer)

    acceleration: Mapped[Decimal] = mapped_column(Numeric(4, 2))

    top_speed: Mapped[int | None] = mapped_column(Integer)

    price_modifier: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    fuel_type: Mapped[str | None] = mapped_column(String(50), default="Petrol")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="engines", lazy="raise")
