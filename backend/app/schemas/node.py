from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    address: str = Field(..., min_length=1, max_length=255)
    api_port: int = Field(50051, ge=1, le=65535)
    api_protocol: str = Field("grpc", pattern="^(grpc|rest)$")
    api_key: str = Field(..., min_length=16)
    usage_ratio: float = Field(1.0, ge=0.1, le=10.0)
    traffic_limit_bytes: Optional[int] = None
    traffic_notify_percent: int = Field(80, ge=0, le=100)
    country_code: Optional[str] = Field(None, max_length=2)
    view_position: int = 0
    add_host_to_inbounds: bool = False


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    api_port: Optional[int] = Field(None, ge=1, le=65535)
    api_protocol: Optional[str] = Field(None, pattern="^(grpc|rest)$")
    api_key: Optional[str] = None
    usage_ratio: Optional[float] = Field(None, ge=0.1, le=10.0)
    traffic_limit_bytes: Optional[int] = None
    traffic_notify_percent: Optional[int] = Field(None, ge=0, le=100)
    is_enabled: Optional[bool] = None
    country_code: Optional[str] = None
    view_position: Optional[int] = None
    add_host_to_inbounds: Optional[bool] = None


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    address: str
    api_port: int
    api_protocol: str
    usage_ratio: float
    traffic_limit_bytes: Optional[int] = None
    traffic_used_bytes: int
    traffic_notify_percent: int
    is_connected: bool
    is_enabled: bool
    xray_running: bool
    xray_version: Optional[str] = None
    node_version: Optional[str] = None
    core_type: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_model: Optional[str] = None
    total_ram_mb: Optional[int] = None
    country_code: Optional[str] = None
    view_position: int
    add_host_to_inbounds: bool
    last_status_message: Optional[str] = None
    last_connected_at: Optional[datetime] = None
    uptime_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime
