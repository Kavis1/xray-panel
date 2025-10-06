from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, JSON, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Inbound(Base):
    __tablename__ = "inbounds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tag: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    
    # Protocol
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # vless, vmess, trojan, ss
    
    # Network
    listen: Mapped[str] = mapped_column(String(64), default="0.0.0.0", nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    network: Mapped[str] = mapped_column(String(20), default="tcp", nullable=False)  # tcp, ws, grpc, h2, quic
    
    # Security
    security: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # tls, reality, none
    
    # TLS Settings
    tls_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Reality Settings
    reality_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Stream Settings
    stream_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Sniffing
    sniffing_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sniffing_dest_override: Mapped[Optional[List[str]]] = mapped_column(
        JSON, default=["http", "tls"]
    )
    domain_strategy: Mapped[Optional[str]] = mapped_column(
        String(32), default="ForceIPv4", nullable=True
    )
    
    # Fallbacks
    fallbacks: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Excluded nodes
    excluded_nodes: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Traffic Control
    block_torrents: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
