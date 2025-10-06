from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, BigInteger, Boolean, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # API Connection
    api_port: Mapped[int] = mapped_column(Integer, default=50051, nullable=False)
    api_protocol: Mapped[str] = mapped_column(
        String(10), default="grpc", nullable=False
    )  # grpc or rest
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # TLS/Certificates
    ssl_cert: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ssl_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ssl_ca: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Usage
    usage_ratio: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Traffic limits
    traffic_limit_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    traffic_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    traffic_notify_percent: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    
    # Status
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    xray_running: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Node Info
    xray_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    node_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    core_type: Mapped[Optional[str]] = mapped_column(String(32), default="xray", nullable=True)
    
    # Hardware
    cpu_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_ram_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    view_position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    add_host_to_inbounds: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    last_status_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
