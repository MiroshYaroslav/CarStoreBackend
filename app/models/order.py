from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseDB

if TYPE_CHECKING:
    from app.models.order_item import OrderItem
    from app.models.user import User


class Order(BaseDB):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    status: Mapped[str] = mapped_column(String(50), default="pending")

    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    first_name: Mapped[str | None] = mapped_column(String(100))

    last_name: Mapped[str | None] = mapped_column(String(100))

    email: Mapped[str | None] = mapped_column(String(255))

    phone: Mapped[str | None] = mapped_column(String(20))

    address: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="raise"
    )

    user: Mapped["User"] = relationship(back_populates="orders", lazy="raise")
