"""create tasks table

Revision ID: 74ff62974915
Revises:
Create Date: 2026-11-12 17:31:18.828007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic；这些 ID 用来串起迁移依赖链。
revision: str = '74ff62974915'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """将数据库升级到本迁移对应的结构。"""
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """将数据库回退到本迁移之前的结构。"""
    op.drop_table("tasks")
