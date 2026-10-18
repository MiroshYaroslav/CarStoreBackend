from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseDB

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product
    from app.models.product_color import ProductColor
    from app.models.product_engine import ProductEngine
    from app.models.product_trim import ProductTrim


class OrderItem(BaseDB):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), index=True
    )

    engine_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_engine.id", ondelete="SET NULL"), index=True
    )

    color_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_color.id", ondelete="SET NULL"), index=True
    )

    trim_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_trim.id", ondelete="SET NULL"), index=True
    )

    quantity: Mapped[int] = mapped_column(Integer)

    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    configuration_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="items", lazy="raise")

    product: Mapped["Product"] = relationship(lazy="raise")

    engine: Mapped["ProductEngine"] = relationship(lazy="raise")

    color: Mapped["ProductColor"] = relationship(lazy="raise")

    trim: Mapped["ProductTrim"] = relationship(lazy="raise")
