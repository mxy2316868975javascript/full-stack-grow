from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import TaskDB


def _owner_filters(
    user_id: int,
    completed: bool | None,
    priority: int | None,
):
    """构造任务列表和总数查询共用的用户与筛选条件。"""

    filters = [TaskDB.owner_id == user_id]
    if completed is not None:
        filters.append(TaskDB.completed == completed)
    if priority is not None:
        filters.append(TaskDB.priority == priority)
    return filters


def add_task(db: Session, task: TaskDB) -> TaskDB:
    """把新任务加入当前 Session，实际提交由 Service 负责。"""

    db.add(task)
    return task


def list_by_owner(
    db: Session,
    user_id: int,
    offset: int,
    limit: int,
    completed: bool | None = None,
    priority: int | None = None,
) -> list[TaskDB]:
    """按用户和可选条件读取一页任务，按主键排序保证结果稳定。"""

    return db.scalars(
        select(TaskDB)
        .where(*_owner_filters(user_id, completed, priority))
        .order_by(TaskDB.id)
        .offset(offset)
        .limit(limit)
    ).all()


def count_by_owner(
    db: Session,
    user_id: int,
    completed: bool | None = None,
    priority: int | None = None,
) -> int:
    """统计筛选后的用户任务总数，供分页元数据使用。"""

    return db.scalar(
        select(func.count())
        .select_from(TaskDB)
        .where(*_owner_filters(user_id, completed, priority))
    ) or 0


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
