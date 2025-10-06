from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class InboundCreate(BaseModel):
    tag: str = Field(..., min_length=1, max_length=64)
    type: str = Field(..., description="vless, vmess, trojan, shadowsocks, hysteria2")
    listen: str = "0.0.0.0"
    port: int = Field(..., ge=1, le=65535)
    network: str = "tcp"
    security: Optional[str] = None
    tls_settings: Optional[Dict[str, Any]] = None
    reality_settings: Optional[Dict[str, Any]] = None
    stream_settings: Optional[Dict[str, Any]] = None
    sniffing_enabled: bool = True
    sniffing_dest_override: Optional[List[str]] = ["http", "tls"]
    domain_strategy: Optional[str] = "ForceIPv4"
    fallbacks: Optional[List[Dict[str, Any]]] = None
    block_torrents: bool = False
    remark: Optional[str] = None
    
    @field_validator('security')
    @classmethod
    def validate_security(cls, v, info):
        """Валидация безопасности: VLESS только с Reality или TLS"""
        inbound_type = info.data.get('type', '').upper()
        
        # VLESS должен иметь Reality или TLS
        if inbound_type == 'VLESS':
            if v not in ['reality', 'tls']:
                raise ValueError('VLESS требует security="reality" или "tls" для безопасности')
        
        # VMESS с WebSocket требует TLS
        if inbound_type == 'VMESS' and info.data.get('network') == 'ws':
            if v != 'tls':
                raise ValueError('VMess WebSocket требует security="tls" для безопасности')
        
        # Trojan всегда требует TLS
        if inbound_type == 'TROJAN' and v != 'tls':
            raise ValueError('Trojan требует security="tls"')
        
        return v


class InboundUpdate(BaseModel):
    tag: Optional[str] = None
    type: Optional[str] = None
    listen: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    network: Optional[str] = None
    security: Optional[str] = None
    tls_settings: Optional[Dict[str, Any]] = None
    reality_settings: Optional[Dict[str, Any]] = None
    stream_settings: Optional[Dict[str, Any]] = None
    sniffing_enabled: Optional[bool] = None
    sniffing_dest_override: Optional[List[str]] = None
    domain_strategy: Optional[str] = None
    fallbacks: Optional[List[Dict[str, Any]]] = None
    is_enabled: Optional[bool] = None
    block_torrents: Optional[bool] = None
    remark: Optional[str] = None


class InboundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tag: str
    type: str
    listen: str
    port: int
    network: str
    security: Optional[str] = None
    tls_settings: Optional[Dict[str, Any]] = None
    reality_settings: Optional[Dict[str, Any]] = None
    stream_settings: Optional[Dict[str, Any]] = None
    sniffing_enabled: bool
    sniffing_dest_override: Optional[List[str]] = None
    domain_strategy: Optional[str] = None
    fallbacks: Optional[List[Dict[str, Any]]] = None
    excluded_nodes: Optional[List[str]] = None
    remark: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
