from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, JSON, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Event filters
    events: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Stats
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_delivery_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WebhookQueue(Base):
    __tablename__ = "webhook_queue"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    webhook_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    tries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_tries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    next_try_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, success, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
