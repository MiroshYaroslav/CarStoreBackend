from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseDB


class CallbackRequest(BaseDB):
    __tablename__ = "callback_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    name: Mapped[str | None] = mapped_column(String(100))

    phone: Mapped[str] = mapped_column(String(20))

    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(50), default="new")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
