from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class UserDB(Base):
    """用户表模型，保存登录所需的用户名和密码哈希。"""

    __tablename__ = "users"

    # 数据库自动递增的用户主键，也是 JWT 中保存的用户身份标识。
    id: Mapped[int] = mapped_column(primary_key=True)
    # 用户名必须唯一，并建立索引以加快登录时的查询。
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )
    # 只保存不可逆的密码哈希，绝不保存用户输入的明文密码。
    password_hash: Mapped[str] = mapped_column(String(255))


class TaskDB(Base):
    """任务表模型，保存任务内容、状态、优先级和所属用户。"""

    __tablename__ = "tasks"

    # 任务主键，用于定位单条任务。
    id: Mapped[int] = mapped_column(primary_key=True)
    # 任务标题，数据库最多保存 100 个字符。
    title: Mapped[str] = mapped_column(String(100))
    # 任务详细说明，可以为空。
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 是否已完成；新任务默认未完成。
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # 任务优先级，默认值为 0，数据库默认值用于兼容旧数据。
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    # 所属用户的 ID；外键保证它只能指向 users.id。
    # 允许为空是为了兼容鉴权功能上线前已经存在的旧任务。
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
