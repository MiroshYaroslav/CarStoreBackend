"""associate reviews with their author

Revision ID: 8ac47d1e2f30
Revises: 7b1c2d3e4f50
Create Date: 2026-10-22 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8ac47d1e2f30"
down_revision: Union[str, Sequence[str], None] = "7b1c2d3e4f50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "review",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_review_user_id_users",
        "review",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_review_user_id", "review", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_review_user_id", table_name="review")
    op.drop_constraint("fk_review_user_id_users", "review", type_="foreignkey")
    op.drop_column("review", "user_id")
