from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    is_sudo: bool = False
    roles: Optional[List[str]] = []


class AdminUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=6)
    is_sudo: Optional[bool] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    is_sudo: bool
    is_active: bool
    roles: List[str]
    mfa_enabled: bool
    telegram_id: Optional[int] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
