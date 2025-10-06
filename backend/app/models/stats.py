from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, func, ForeignKey, Date, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class StatsUserDaily(Base):
    __tablename__ = "stats_user_daily"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    
    bytes_uploaded: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_downloaded: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    resets_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StatsInboundDaily(Base):
    __tablename__ = "stats_inbound_daily"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inbound_tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    
    bytes_uploaded: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_downloaded: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StatsSystemNode(Base):
    __tablename__ = "stats_system_node"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    
    # CPU
    cpu_cores: Mapped[int] = mapped_column(Integer, nullable=False)
    cpu_usage_percent: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Memory
    mem_total_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    mem_used_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    mem_usage_percent: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Network
    net_rx_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    net_tx_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
