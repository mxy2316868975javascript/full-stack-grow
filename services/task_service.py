from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from errors import ValidationError
from models import TaskDB
from repositories import task_repository
from schemas import TaskCreate, TaskUpdate


def create_task(
    db: Session,
    user_id: int,
    payload: TaskCreate,
) -> TaskDB:
    """为指定用户创建任务并提交事务，失败时回滚。"""

    task = TaskDB(
        **payload.model_dump(),
        owner_id=user_id,
    )

    try:
        task_repository.add_task(db, task)
        db.commit()
        db.refresh(task)
        return task
    except SQLAlchemyError:
        db.rollback()
        raise


def list_tasks(db: Session, user_id: int) -> list[TaskDB]:
    """只查询指定用户拥有的任务，避免跨用户读取数据。"""

    return task_repository.list_by_owner(db, user_id)


def get_owned_task(
    db: Session,
    user_id: int,
    task_id: int,
) -> TaskDB | None:
    """按任务 ID 和用户 ID 查询任务，确保任务属于当前用户。"""

    return task_repository.get_by_owner(db, user_id, task_id)


def update_task(
    db: Session,
    user_id: int,
    task_id: int,
    payload: TaskUpdate,
) -> TaskDB | None:
    """更新当前用户的任务；找不到任务时返回 None，失败时回滚。"""

    task = get_owned_task(db, user_id, task_id)
    if task is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if "title" in updates and updates["title"] is None:
        raise ValidationError("title cannot be null")

    for field, value in updates.items():
        setattr(task, field, value)

    try:
        db.commit()
        db.refresh(task)
        return task
    except SQLAlchemyError:
        db.rollback()
        raise


def delete_task(db: Session, user_id: int, task_id: int) -> bool:
    """删除当前用户的任务，并返回是否找到并删除了任务。"""

    task = get_owned_task(db, user_id, task_id)
    if task is None:
        return False

    try:
        task_repository.remove_task(db, task)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
