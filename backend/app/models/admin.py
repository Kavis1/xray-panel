from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    is_sudo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    roles: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    telegram_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
