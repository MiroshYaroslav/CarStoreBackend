from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseDB

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.product_color import ProductColor
    from app.models.product_engine import ProductEngine
    from app.models.product_trim import ProductTrim


class CartItem(BaseDB):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    session_id: Mapped[str | None] = mapped_column(String(255), index=True)

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), index=True
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

    quantity: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR session_id IS NOT NULL", name="chk_user_or_session"
        ),
    )

    product: Mapped["Product"] = relationship(lazy="raise")

    engine: Mapped["ProductEngine"] = relationship(lazy="raise")

    color: Mapped["ProductColor"] = relationship(lazy="raise")

    trim: Mapped["ProductTrim"] = relationship(lazy="raise")
