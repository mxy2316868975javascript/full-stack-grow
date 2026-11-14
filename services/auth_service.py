import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import UserDB
from repositories import user_repository
from schemas import UserCreate


JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-later")
# HS256 用于本地学习；生产环境应选择合适的密钥管理方案。
JWT_ALGORITHM = "HS256"
# 令牌有效期，过期后客户端需要重新登录。
JWT_EXPIRE_MINUTES = 30

# FastAPI 从 Authorization: Bearer <token> 请求头中提取 JWT。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """将明文密码转换为不可逆哈希，供数据库保存。"""

    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """验证用户输入的密码是否匹配数据库中的哈希。"""

    return password_hash.verify(password, hashed_password)


def register(db: Session, payload: UserCreate) -> UserDB:
    """注册用户、哈希密码并提交事务；数据库失败时回滚。"""

    if user_repository.get_by_username(db, payload.username) is not None:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    user = UserDB(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )

    try:
        user_repository.add_user(db, user)
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback()
        raise


def login(db: Session, username: str, password: str) -> dict[str, str]:
    """验证用户密码并返回 Bearer JWT。"""

    user = user_repository.get_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )
    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": expires_at,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserDB:
    """解析 JWT 并根据 token 中的用户 ID 返回当前用户。"""

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_repository.get_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
