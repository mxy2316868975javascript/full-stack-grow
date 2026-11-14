class AppError(Exception):
    """应用层可预期错误的基类。"""

    def __init__(
        self,
        detail: str,
        status_code: int,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(detail)
        # 返回给客户端的安全错误描述。
        self.detail = detail
        # HTTP 响应状态码，例如 401、404 或 422。
        self.status_code = status_code
        # 需要额外返回的响应头，例如 Bearer 鉴权提示。
        self.headers = headers or {}


class AuthenticationError(AppError):
    """用户名、密码或令牌无效时使用的 401 错误。"""

    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(
            detail=detail,
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictError(AppError):
    """请求与已有数据冲突时使用的 409 错误。"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409)


class NotFoundError(AppError):
    """请求的资源不存在或不属于当前用户时使用的 404 错误。"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)


class ValidationError(AppError):
    """业务参数不符合规则时使用的 422 错误。"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=422)
