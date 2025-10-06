from typing import Any, List, Optional
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./panel.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    DOCS_ENABLED: bool = True
    PROJECT_NAME: str = "Xray Control Panel"
    VERSION: str = "0.1.0"
    
    # Subscription
    XRAY_SUBSCRIPTION_URL_PREFIX: str = "https://panel.example.com/sub"
    SUBSCRIPTION_CACHE_TTL: int = 300
    
    # HWID Device Limit
    HWID_DEVICE_LIMIT_ENABLED: bool = True
    HWID_FALLBACK_DEVICE_LIMIT: int = 3
    HWID_MAX_DEVICES_ANNOUNCE: int = 5
    
    # Webhooks
    WEBHOOK_SECRET_HEADER: str = "your-webhook-secret"
    WEBHOOK_MAX_RETRIES: int = 3
    JOB_SEND_NOTIFICATIONS_INTERVAL: int = 30
    
    # Telegram Bot (опционально)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ADMIN_IDS: List[int] = []
    TELEGRAM_ENABLED: bool = False
    
    @field_validator("TELEGRAM_ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> List[int]:
        if isinstance(v, str):
            return [int(id.strip()) for id in v.split(",") if id.strip()]
        return v
    
    @field_validator("TELEGRAM_ENABLED", mode="before")
    @classmethod
    def check_telegram_enabled(cls, v: Any, info) -> bool:
        # Автоматически включаем если задан токен
        if hasattr(info, 'data') and info.data.get('TELEGRAM_BOT_TOKEN'):
            return True
        return v
    
    # Xray
    XRAY_EXECUTABLE_PATH: str = "/usr/local/bin/xray"
    XRAY_ASSETS_PATH: str = "/usr/local/share/xray"
    
    # Workers
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
