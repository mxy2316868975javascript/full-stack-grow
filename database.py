from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from config import BASE_DIR, settings

# 静态前端资源目录，由 main.py 挂载到 /static。
STATIC_DIR = BASE_DIR / "static"

# 使用绝对路径，避免从其他目录启动时创建出另一份数据库。
# check_same_thread=False 允许 FastAPI 的工作线程使用同一个 SQLite 引擎。
engine_options = {}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)


class Base(DeclarativeBase):
    """所有 SQLAlchemy 数据库模型的基类。"""

    pass


def get_db():
    """为一次请求提供数据库 Session，并在请求结束后关闭它。"""

    with Session(engine) as session:
        yield session
