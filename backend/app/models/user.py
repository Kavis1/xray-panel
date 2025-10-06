from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import String, Integer, BigInteger, Boolean, JSON, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    LIMITED = "LIMITED"
    EXPIRED = "EXPIRED"


class TrafficLimitStrategy(str, Enum):
    NO_RESET = "NO_RESET"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class ProxyType(str, Enum):
    VMESS = "VMESS"
    VLESS = "VLESS"
    TROJAN = "TROJAN"
    SHADOWSOCKS = "SHADOWSOCKS"
    HYSTERIA = "HYSTERIA"
    HYSTERIA2 = "HYSTERIA2"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    status: Mapped[str] = mapped_column(
        String(20), default=UserStatus.ACTIVE.value, nullable=False, index=True
    )
    
    # Traffic limits
    traffic_limit_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    traffic_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    traffic_limit_strategy: Mapped[str] = mapped_column(
        String(20), default=TrafficLimitStrategy.NO_RESET.value, nullable=False
    )
    last_traffic_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Expiration
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Subscription
    sub_revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sub_last_user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # HWID
    hwid_device_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Connection Limit
    max_connections: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    online_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # Relationships
    proxies: Mapped[List["UserProxy"]] = relationship(
        "UserProxy", back_populates="user", cascade="all, delete-orphan"
    )
    inbounds: Mapped[List["UserInbound"]] = relationship(
        "UserInbound", back_populates="user", cascade="all, delete-orphan"
    )
    hwid_devices: Mapped[List["HwidDevice"]] = relationship(
        "HwidDevice", back_populates="user", cascade="all, delete-orphan"
    )


class UserProxy(Base):
    __tablename__ = "user_proxies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # ProxyType
    
    # Credentials
    vmess_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    vless_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    vless_flow: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    trojan_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ss_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ss_method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    hysteria_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hysteria2_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Transport
    network: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # tcp, ws, grpc, quic, h2
    security: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # tls, reality, null
    
    # TLS/Reality
    sni: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    alpn: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    # Additional settings
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="proxies")


class UserInbound(Base):
    __tablename__ = "user_inbounds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inbound_tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="inbounds")


class HwidDevice(Base):
    __tablename__ = "hwid_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    hwid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_os: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ver_os: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    device_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="hwid_devices")
