from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from errors import AppError


def register_exception_handlers(app: FastAPI) -> None:
    """为应用注册业务异常和数据库异常的统一响应处理器。"""

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError):
        """把可预期业务异常转换为统一的 JSON 响应。"""

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(_request: Request, _exc: SQLAlchemyError):
        """隐藏数据库内部细节，避免把 SQL 或表结构泄露给客户端。"""

        return JSONResponse(
            status_code=500,
            content={"detail": "Database operation failed"},
        )
