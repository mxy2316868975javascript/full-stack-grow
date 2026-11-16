import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    """应用运行配置，统一从环境变量读取并在启动时固定下来。"""

    # SQLAlchemy 使用的数据库连接地址。
    database_url: str
    # JWT 签名密钥，生产环境必须从环境变量注入。
    jwt_secret: str
    # JWT 使用的签名算法。
    jwt_algorithm: str
    # JWT 从签发开始可以使用多少分钟。
    jwt_expire_minutes: int
    # 允许跨域访问 API 的前端地址，多个地址用逗号分隔。
    cors_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        """从环境变量构造配置；未设置时使用本地学习默认值。"""

        default_database_url = f"sqlite:///{BASE_DIR / 'tasks_migration.db'}"
        return cls(
            database_url=os.getenv("DATABASE_URL", default_database_url),
            jwt_secret=os.getenv(
                "JWT_SECRET",
                "dev-only-secret-change-later",
            ),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expire_minutes=int(
                os.getenv("JWT_EXPIRE_MINUTES", "30")
            ),
            cors_origins=tuple(
                origin.strip()
                for origin in os.getenv(
                    "CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173,"
                    "http://localhost:5174,http://127.0.0.1:5174",
                ).split(",")
                if origin.strip()
            ),
        )


settings = Settings.from_environment()
