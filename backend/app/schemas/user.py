from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.user import UserStatus, TrafficLimitStrategy, ProxyType


class ProxyBase(BaseModel):
    type: ProxyType
    network: Optional[str] = None
    security: Optional[str] = None
    sni: Optional[str] = None
    alpn: Optional[List[str]] = None
    fingerprint: Optional[str] = None


class ProxyCreate(ProxyBase):
    vmess_uuid: Optional[str] = None
    vless_uuid: Optional[str] = None
    vless_flow: Optional[str] = None
    trojan_password: Optional[str] = None
    ss_password: Optional[str] = None
    ss_method: Optional[str] = None


class ProxyResponse(ProxyBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    vmess_uuid: Optional[str] = None
    vless_uuid: Optional[str] = None
    vless_flow: Optional[str] = None
    trojan_password: Optional[str] = None
    ss_password: Optional[str] = None
    ss_method: Optional[str] = None
    created_at: datetime


class HwidDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hwid: str
    device_os: Optional[str] = None
    ver_os: Optional[str] = None
    device_model: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    email: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    traffic_limit_bytes: Optional[int] = None
    traffic_limit_strategy: TrafficLimitStrategy = TrafficLimitStrategy.NO_RESET
    expire_at: Optional[datetime] = None
    description: Optional[str] = None
    telegram_id: Optional[int] = None
    hwid_device_limit: Optional[int] = None
    proxies: Optional[List[ProxyCreate]] = []
    inbound_tags: Optional[List[str]] = []


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=0, max_length=128)
    status: Optional[UserStatus] = None
    traffic_limit_bytes: Optional[int] = None
    traffic_limit_strategy: Optional[TrafficLimitStrategy] = None
    expire_at: Optional[datetime] = None
    description: Optional[str] = None
    telegram_id: Optional[int] = None
    hwid_device_limit: Optional[int] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: Optional[str] = None
    status: str
    traffic_limit_bytes: Optional[int] = None
    traffic_used_bytes: int
    traffic_limit_strategy: str
    expire_at: Optional[datetime] = None
    sub_revoked_at: Optional[datetime] = None
    online_at: Optional[datetime] = None
    description: Optional[str] = None
    telegram_id: Optional[int] = None
    hwid_device_limit: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    proxies: List[ProxyResponse] = []
    hwid_devices: List[HwidDeviceResponse] = []


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: Optional[str] = None
    status: str
    traffic_limit_bytes: Optional[int] = None
    traffic_used_bytes: int
    traffic_limit_strategy: str
    expire_at: Optional[datetime] = None
    sub_revoked_at: Optional[datetime] = None
    online_at: Optional[datetime] = None
    description: Optional[str] = None
    telegram_id: Optional[int] = None
    hwid_device_limit: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    total: int
    items: List[UserListItem]
