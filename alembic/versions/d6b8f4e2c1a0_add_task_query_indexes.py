"""add task query indexes

Revision ID: d6b8f4e2c1a0
Revises: 5c546500a267
Create Date: 2026-11-16

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic；复合索引覆盖任务列表的常用查询组合。
revision: str = "d6b8f4e2c1a0"
down_revision: Union[str, Sequence[str], None] = "5c546500a267"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为任务列表的用户过滤、筛选和排序建立复合索引。"""

    op.create_index(
        "ix_tasks_owner_id_id",
        "tasks",
        ["owner_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_owner_id_priority_id",
        "tasks",
        ["owner_id", "priority", "id"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_owner_id_completed_id",
        "tasks",
        ["owner_id", "completed", "id"],
        unique=False,
    )


def downgrade() -> None:
    """移除任务列表查询使用的复合索引。"""

    op.drop_index("ix_tasks_owner_id_completed_id", table_name="tasks")
    op.drop_index("ix_tasks_owner_id_priority_id", table_name="tasks")
    op.drop_index("ix_tasks_owner_id_id", table_name="tasks")
