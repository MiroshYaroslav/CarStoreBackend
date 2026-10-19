from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseDB


class CallbackContact(BaseDB):
    __tablename__ = "callback_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
