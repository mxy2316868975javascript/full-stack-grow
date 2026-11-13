"""add task owner

Revision ID: 5c546500a267
Revises: cbe582b2e6ea
Create Date: 2026-11-12 23:11:19.491596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic；down_revision 指向创建 users 表的迁移。
revision: str = '5c546500a267'
down_revision: Union[str, Sequence[str], None] = 'cbe582b2e6ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """给 tasks 增加 owner_id 外键，并建立按所属用户查询的索引。"""

    # SQLite 不能直接修改约束，batch 模式会通过重建表安全完成变更。
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("owner_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_tasks_owner_id",
            ["owner_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_tasks_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )


def downgrade() -> None:
    """移除任务所属用户字段、索引和外键。"""

    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "fk_tasks_owner_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_tasks_owner_id")
        batch_op.drop_column("owner_id")
