from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


# 当前 Python 文件所在目录，用于构造稳定的项目内路径。
BASE_DIR = Path(__file__).resolve().parent
# 静态前端资源目录，由 main.py 挂载到 /static。
STATIC_DIR = BASE_DIR / "static"

# 使用绝对路径，避免从其他目录启动时创建出另一份数据库。
# check_same_thread=False 允许 FastAPI 的工作线程使用同一个 SQLite 引擎。
engine = create_engine(
    f"sqlite:///{BASE_DIR / 'tasks_migration.db'}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    """所有 SQLAlchemy 数据库模型的基类。"""

    pass


def get_db():
    """为一次请求提供数据库 Session，并在请求结束后关闭它。"""

    with Session(engine) as session:
        yield session
