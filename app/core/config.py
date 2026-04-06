from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Finance Dashboard API"
    app_env: str = "development"
    debug: bool = True

    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "sqlite:///./finance_dashboard.db"

    redis_url: str = "redis://localhost:6379/0"

    rate_limit_requests: int = 60
    rate_limit_window: int = 60

    # Default admin seed credentials (used only on first run)
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin@1234"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
