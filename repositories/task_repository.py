from sqlalchemy import select
from sqlalchemy.orm import Session

from models import TaskDB


def add_task(db: Session, task: TaskDB) -> TaskDB:
    """把新任务加入当前 Session，实际提交由 Service 负责。"""

    db.add(task)
    return task


def list_by_owner(db: Session, user_id: int) -> list[TaskDB]:
    """查询指定用户拥有的全部任务。"""

    return db.scalars(
        select(TaskDB).where(TaskDB.owner_id == user_id)
    ).all()


def get_by_owner(
    db: Session,
    user_id: int,
    task_id: int,
) -> TaskDB | None:
    """按任务 ID 和所属用户 ID 查询任务。"""

    return db.scalar(
        select(TaskDB).where(
            TaskDB.id == task_id,
            TaskDB.owner_id == user_id,
        )
    )


def remove_task(db: Session, task: TaskDB) -> None:
    """把任务标记为删除，实际提交由 Service 负责。"""

    db.delete(task)
