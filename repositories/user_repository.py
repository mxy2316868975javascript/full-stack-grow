from sqlalchemy import select
from sqlalchemy.orm import Session

from models import UserDB


def add_user(db: Session, user: UserDB) -> UserDB:
    """把新用户加入当前 Session，实际提交由认证 Service 负责。"""

    db.add(user)
    return user


def get_by_username(db: Session, username: str) -> UserDB | None:
    """按用户名查询用户，供注册检查和登录验证使用。"""

    return db.scalar(
        select(UserDB).where(UserDB.username == username)
    )


def get_by_id(db: Session, user_id: int) -> UserDB | None:
    """按用户主键查询用户，供 JWT 鉴权恢复当前用户使用。"""

    return db.get(UserDB, user_id)
