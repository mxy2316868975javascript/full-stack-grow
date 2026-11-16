from math import ceil

from fastapi import Depends, FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from errors import NotFoundError
from exception_handlers import register_exception_handlers
from models import UserDB
from schemas import TaskCreate, TaskPage, TaskRead, TaskUpdate, UserCreate, UserRead
from services import auth_service, task_service


app = FastAPI(title="Task API")
register_exception_handlers(app)

# 允许独立运行的前端开发服务器访问 API；生产环境应只配置可信前端域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root():
    """返回 API 入口提示；前端现在由独立的 Vite 应用运行。"""

    return {"service": "Task API", "docs": "/docs"}


@app.get("/health")
def health():
    """返回服务健康状态，供本地或部署环境快速检查。"""

    return {"status": "ok", "service": "Task API"}


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """校验用户名并创建用户，密码只以哈希形式保存。"""

    return auth_service.register(db, payload)


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """验证用户名和密码，并签发带过期时间的 JWT。"""

    return auth_service.login(
        db,
        form_data.username,
        form_data.password,
    )


@app.get("/auth/me", response_model=UserRead)
def get_me(current_user: UserDB = Depends(auth_service.get_current_user)):
    """返回当前令牌对应的用户信息。"""

    return current_user


# 任务路由统一注入当前用户和数据库 Session：前者负责权限，后者负责读写数据库。
@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    current_user: UserDB = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """接收创建请求，并交给 Service 绑定当前用户后保存。"""

    return task_service.create_task(db, current_user.id, payload)


@app.get("/tasks", response_model=TaskPage)
def list_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    completed: bool | None = Query(default=None),
    priority: int | None = Query(default=None, ge=0, le=5),
    current_user: UserDB = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户的一页任务和分页元信息。"""

    tasks, total = task_service.list_tasks(
        db,
        current_user.id,
        page,
        page_size,
        completed,
        priority,
    )
    return {
        "items": tasks,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": ceil(total / page_size),
    }


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    current_user: UserDB = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前用户的一条任务，不允许读取其他用户的任务。"""

    task = task_service.get_owned_task(db, current_user.id, task_id)
    if task is None:
        raise NotFoundError("Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: UserDB = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户的任务，并把业务校验错误转换为 HTTP 422。"""

    task = task_service.update_task(
        db,
        current_user.id,
        task_id,
        payload,
    )

    if task is None:
        raise NotFoundError("Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: UserDB = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """删除当前用户的任务，找不到时返回 HTTP 404。"""

    deleted = task_service.delete_task(db, current_user.id, task_id)
    if not deleted:
        raise NotFoundError("Task not found")
    return Response(status_code=204)
