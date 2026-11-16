from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    """创建任务时接收的请求数据。"""

    # 标题不能为空，长度限制避免无效或过大的输入。
    title: str = Field(min_length=1, max_length=100)
    # 描述是可选的，未提供时保存为空。
    description: str | None = None
    # 优先级限制在 0 到 5，默认使用普通优先级 0。
    priority: int = Field(default=0, ge=0, le=5)


class TaskUpdate(BaseModel):
    """部分更新任务时接收的数据，未提交的字段保持原值。"""

    # None 表示请求中没有提供该字段；实际提交的标题仍不能为空。
    title: str | None = Field(default=None, min_length=1, max_length=100)
    # 描述可以被修改为文本或空值。
    description: str | None = None
    # 完成状态是可选的布尔更新字段。
    completed: bool | None = None
    # 优先级更新仍需遵守 0 到 5 的范围。
    priority: int | None = Field(default=None, ge=0, le=5)


class TaskRead(BaseModel):
    """返回给前端的任务数据，不暴露内部权限字段 owner_id。"""

    model_config = ConfigDict(from_attributes=True)

    # 允许 Pydantic 从 SQLAlchemy 对象读取这些字段。
    id: int
    # 任务标题。
    title: str
    # 任务描述，可能为空。
    description: str | None
    # 当前是否已完成。
    completed: bool
    # 任务优先级。
    priority: int


class TaskPage(BaseModel):
    """任务分页响应，包含当前页数据和分页元信息。"""

    # 当前页任务，任务本身仍然不暴露 owner_id。
    items: list[TaskRead]
    # 当前页码，从 1 开始。
    page: int
    # 每页最多返回的任务数量。
    page_size: int
    # 当前用户的任务总数。
    total: int
    # 按 page_size 计算出的总页数。
    pages: int


class UserCreate(BaseModel):
    """注册用户时接收的用户名和明文密码。"""

    # 用户名长度限制用于基础输入校验。
    username: str = Field(min_length=3, max_length=50)
    # 密码只在请求处理期间存在，随后会被哈希后保存。
    password: str = Field(min_length=6, max_length=100)


class UserRead(BaseModel):
    """返回给前端的用户信息，不包含 password_hash。"""

    model_config = ConfigDict(from_attributes=True)

    # 数据库中的用户主键。
    id: int
    # 可公开展示的用户名。
    username: str
