"""add callback phone contacts

Revision ID: 7b1c2d3e4f50
Revises: 44e6bec0c07e
Create Date: 2026-10-19 21:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7b1c2d3e4f50"
down_revision: Union[str, Sequence[str], None] = "44e6bec0c07e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "callback_contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("number", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    contacts = sa.table(
        "callback_contacts",
        sa.column("number", sa.String(length=20)),
        sa.column("description", sa.String(length=100)),
    )
    op.bulk_insert(
        contacts,
        [
            {"number": "+380501234567", "description": "Відділ продажу"},
            {"number": "+380671234567", "description": "Служба підтримки"},
        ],
    )


def downgrade() -> None:
    op.drop_table("callback_contacts")
