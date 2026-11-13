import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import STATIC_DIR, get_db
from models import UserDB
from schemas import TaskCreate, TaskRead, TaskUpdate, UserCreate, UserRead
from services import task_service


JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-later")
# JWT 签名密钥；生产环境必须通过环境变量提供随机且保密的值。
# JWT_SECRET 的默认值只用于本地学习，不能用于线上服务。
JWT_ALGORITHM = "HS256"
# 令牌有效期，过期后客户端必须重新登录。
JWT_EXPIRE_MINUTES = 30

# FastAPI 用它从 Authorization: Bearer <token> 请求头中提取令牌。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# 使用 pwdlib 推荐的 Argon2 配置处理密码哈希。
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """将明文密码转换为不可逆哈希，供数据库保存。"""

    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """验证用户输入的密码是否匹配数据库中的哈希。"""

    return password_hash.verify(password, hashed_password)


app = FastAPI(title="Task API")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    """返回静态前端页面。"""

    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    """返回服务健康状态，供本地或部署环境快速检查。"""

    return {"status": "ok", "service": "Task API"}


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """校验用户名并创建用户，密码只以哈希形式保存。"""

    existing_user = db.scalar(
        select(UserDB).where(UserDB.username == payload.username)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    user = UserDB(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """验证用户名和密码，并签发带过期时间的 JWT。"""

    user = db.scalar(
        select(UserDB).where(UserDB.username == form_data.username)
    )

    if user is None or not verify_password(
        form_data.password,
        user.password_hash,
    ):
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
):
    """解析 Bearer JWT，并根据 token 中的用户 ID 查出当前用户。"""

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

    user = db.get(UserDB, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@app.get("/auth/me", response_model=UserRead)
def get_me(current_user: UserDB = Depends(get_current_user)):
    """返回当前令牌对应的用户信息。"""

    return current_user


# 任务路由统一注入当前用户和数据库 Session：前者负责权限，后者负责读写数据库。
@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """接收创建请求，并交给 Service 绑定当前用户后保存。"""

    return task_service.create_task(db, current_user.id, payload)


@app.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户拥有的任务列表。"""

    return task_service.list_tasks(db, current_user.id)


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前用户的一条任务，不允许读取其他用户的任务。"""

    task = task_service.get_owned_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户的任务，并把业务校验错误转换为 HTTP 422。"""

    try:
        task = task_service.update_task(
            db,
            current_user.id,
            task_id,
            payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除当前用户的任务，找不到时返回 HTTP 404。"""

    deleted = task_service.delete_task(db, current_user.id, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
