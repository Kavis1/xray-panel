from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, func, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class APIKey(Base):
    """API ключи для внешних приложений"""
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Ключ и метаданные
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Права доступа
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)  # {"users": ["read", "write"], "nodes": ["read"]}
    scopes: Mapped[list] = mapped_column(JSON, default=list)  # ["users:read", "users:write", "subscriptions:read"]
    
    # Rate limiting
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=60)
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1000)
    
    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Дополнительные ограничения
    allowed_ips: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Список разрешенных IP
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Статистика использования
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Связь с администратором
    created_by_admin_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
