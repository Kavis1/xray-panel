from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.base import get_db
from app.models.user import User, UserInbound
from app.models.inbound import Inbound
from app.models.settings import Settings
from app.core.config import settings
import base64
import json
from urllib.parse import quote
from typing import List, Dict, Any

router = APIRouter()


def generate_subscription_links(user: User, inbounds: List[Inbound], username_tag: str = "") -> List[str]:
    """Generate subscription links for user's proxies and inbounds"""
    links = []
    
    # Get server address from settings
    server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
    
    for proxy in user.proxies:
        for inbound in inbounds:
            # Match proxy type with inbound type
            proxy_type_map = {
                "VLESS": "vless",
                "VMESS": "vmess",
                "TROJAN": "trojan",
                "SHADOWSOCKS": "shadowsocks",
                "HYSTERIA": "hysteria",
                "HYSTERIA2": "hysteria2"
            }
            
            if proxy.type.upper() not in proxy_type_map:
                continue
                
            # Compare types case-insensitively
            if proxy_type_map[proxy.type.upper()] != inbound.type.lower():
                continue
            
            # Generate link based on type (case-insensitive)
            proxy_type_upper = proxy.type.upper()
            if proxy_type_upper == "VLESS" and proxy.vless_uuid:
                link = generate_vless_link(proxy, inbound, server, username_tag)
            elif proxy_type_upper == "VMESS" and proxy.vmess_uuid:
                link = generate_vmess_link(proxy, inbound, server, username_tag)
            elif proxy_type_upper == "TROJAN" and proxy.trojan_password:
                link = generate_trojan_link(proxy, inbound, server, username_tag)
            elif proxy_type_upper == "SHADOWSOCKS" and proxy.ss_password:
                link = generate_ss_link(proxy, inbound, server, username_tag)
            elif proxy_type_upper == "HYSTERIA" and proxy.vmess_uuid:
                link = generate_hysteria_link(proxy, inbound, server, username_tag)
            elif proxy_type_upper == "HYSTERIA2" and proxy.vmess_uuid:
                link = generate_hysteria2_link(proxy, inbound, server, username_tag)
            else:
                continue
                
            if link:
                links.append(link)
    
    return links


def generate_vless_link(proxy, inbound, server: str, username_tag: str = "") -> str:
    """Generate VLESS link"""
    params = {
        "type": inbound.network or "tcp",
        "security": inbound.security or "none",
    }
    
    # Add Reality settings if present
    if inbound.security == "reality" and inbound.stream_settings:
        reality = inbound.stream_settings.get("reality_settings", {})
        if reality.get("server_names"):
            params["sni"] = reality["server_names"][0]
        if reality.get("short_ids"):
            params["sid"] = reality["short_ids"][0]
        if proxy.fingerprint:
            params["fp"] = proxy.fingerprint
        if proxy.vless_flow:
            params["flow"] = proxy.vless_flow
        params["pbk"] = reality.get("public_key", "")
    
    # Add TLS settings if present
    elif inbound.security == "tls" and proxy.sni:
        params["sni"] = proxy.sni
        if proxy.alpn:
            params["alpn"] = ",".join(proxy.alpn)
        if proxy.fingerprint:
            params["fp"] = proxy.fingerprint
    
    query = "&".join([f"{k}={quote(str(v))}" for k, v in params.items() if v])
    remark = f"{inbound.remark or inbound.tag}{username_tag}"
    
    return f"vless://{proxy.vless_uuid}@{server}:{inbound.port}?{query}#{quote(remark)}"


def generate_vmess_link(proxy, inbound, server: str, username_tag: str = "") -> str:
    """Generate VMess link"""
    import json
    
    config = {
        "v": "2",
        "ps": f"{inbound.remark or inbound.tag}{username_tag}",
        "add": server,
        "port": inbound.port,
        "id": proxy.vmess_uuid,
        "aid": 0,
        "net": inbound.network or "tcp",
        "type": "none",
        "host": "",
        "path": "",
        "tls": inbound.security or "none",
        "sni": proxy.sni or "",
        "alpn": ",".join(proxy.alpn) if proxy.alpn else ""
    }
    
    json_str = json.dumps(config)
    encoded = base64.b64encode(json_str.encode()).decode()
    return f"vmess://{encoded}"


def generate_trojan_link(proxy, inbound, server: str, username_tag: str = "") -> str:
    """Generate Trojan link"""
    params = {}
    
    if inbound.security == "tls" and proxy.sni:
        params["sni"] = proxy.sni
    if proxy.alpn:
        params["alpn"] = ",".join(proxy.alpn)
    
    query = "&".join([f"{k}={quote(str(v))}" for k, v in params.items() if v])
    query_str = f"?{query}" if query else ""
    remark = f"{inbound.remark or inbound.tag}{username_tag}"
    
    return f"trojan://{proxy.trojan_password}@{server}:{inbound.port}{query_str}#{quote(remark)}"


def generate_ss_link(proxy, inbound, server: str, username_tag: str = "") -> str:
    """Generate Shadowsocks link"""
    # Format: ss://base64(method:password)@server:port#remark
    method = proxy.ss_method or "aes-256-gcm"
    credentials = f"{method}:{proxy.ss_password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    remark = f"{inbound.remark or inbound.tag}{username_tag}"
    
    return f"ss://{encoded}@{server}:{inbound.port}#{quote(remark)}"


def generate_hysteria_link(proxy, inbound, server: str, username_tag: str = "") -> str:
    """Generate Hysteria link"""
    remark = f"{inbound.remark or inbound.tag}{username_tag}"
    # Hysteria format: hysteria://server:port?auth=password&upmbps=X&downmbps=Y#remark
    auth = proxy.vmess_uuid or "password"
    return f"hysteria://{server}:{inbound.port}?auth={auth}&upmbps=100&downmbps=100#{quote(remark)}"


def generate_hysteria2_link(proxy, inbound, server: str, username_tag: str = "") -> str:
    """Generate Hysteria2 link"""
    remark = f"{inbound.remark or inbound.tag}{username_tag}"
    # Hysteria2 format: hysteria2://password@server:port#remark
    auth = proxy.vmess_uuid or "password"
    return f"hysteria2://{auth}@{server}:{inbound.port}#{quote(remark)}"


@router.get("/{token}")
async def get_subscription(
    token: str,
    db: AsyncSession = Depends(get_db),
    user_agent: str = Header(None),
):
    # Load user with proxies by subscription_token
    result = await db.execute(
        select(User)
        .options(selectinload(User.proxies))
        .where(User.subscription_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    if user.sub_revoked_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription has been revoked",
        )
    
    # Get user's inbound tags
    result = await db.execute(
        select(UserInbound.inbound_tag)
        .where(UserInbound.user_id == user.id)
    )
    inbound_tags = [row[0] for row in result.all()]
    
    if not inbound_tags:
        # Return empty subscription
        content = base64.b64encode(b"").decode()
        return Response(content=content, media_type="text/plain")
    
    # Get username tag from settings
    username_tag = ""
    tag_setting = await db.execute(
        select(Settings).where(Settings.key == "username_tag")
    )
    tag_setting = tag_setting.scalar_one_or_none()
    if tag_setting and tag_setting.value:
        username_tag = f" {tag_setting.value}"
    
    # Get inbounds
    result = await db.execute(
        select(Inbound)
        .where(Inbound.tag.in_(inbound_tags))
        .where(Inbound.is_enabled == True)
    )
    inbounds = result.scalars().all()
    
    if not inbounds:
        # Return empty subscription
        content = base64.b64encode(b"").decode()
        return Response(content=content, media_type="text/plain")
    
    # Generate links
    links = generate_subscription_links(user, inbounds, username_tag)
    
    if not links:
        # Return empty subscription
        content = base64.b64encode(b"").decode()
        return Response(content=content, media_type="text/plain")
    
    # Return base64 encoded links
    content = "\n".join(links)
    encoded = base64.b64encode(content.encode()).decode()
    
    return Response(content=encoded, media_type="text/plain")


def generate_singbox_outbound(proxy, inbound, server: str, username_tag: str = "", idx: int = 0) -> Dict[str, Any]:
    """Generate sing-box outbound WITHOUT disable_sni"""
    tag = f"{inbound.remark or inbound.tag}{username_tag} § {idx}"
    
    if proxy.type == "VLESS" and proxy.vless_uuid:
        outbound = {
            "type": "vless",
            "tag": tag,
            "server": server,
            "server_port": inbound.port,
            "uuid": proxy.vless_uuid,
            "packet_encoding": "xudp"
        }
        
        # Add flow ONLY for Reality (not for regular TLS or WebSocket)
        # XTLS Vision is deprecated in newer Xray versions
        if proxy.vless_flow and inbound.network != "ws" and inbound.security == "reality":
            outbound["flow"] = proxy.vless_flow
        
        # Add TLS/Reality settings
        if inbound.security in ["tls", "reality"]:
            tls_config = {
                "enabled": True
            }
            
            # Add SNI
            if inbound.security == "reality" and inbound.stream_settings:
                reality = inbound.stream_settings.get("reality_settings", {})
                if reality.get("server_names"):
                    tls_config["server_name"] = reality["server_names"][0]
            elif proxy.sni:
                tls_config["server_name"] = proxy.sni
            else:
                # Default server name for TLS
                tls_config["server_name"] = server
            
            # Add uTLS without disable_sni
            if proxy.fingerprint or inbound.security == "reality":
                tls_config["utls"] = {
                    "enabled": True,
                    "fingerprint": proxy.fingerprint or "chrome"
                }
            
            # Add Reality settings (REQUIRED for Reality security)
            if inbound.security == "reality":
                if inbound.stream_settings:
                    reality = inbound.stream_settings.get("reality_settings", {})
                    if reality.get("public_key") and reality.get("short_ids"):
                        tls_config["reality"] = {
                            "enabled": True,
                            "public_key": reality["public_key"],
                            "short_id": reality["short_ids"][0] if reality["short_ids"] else ""
                        }
                    else:
                        # Skip this inbound if Reality settings are incomplete
                        return {}
                else:
                    # Skip if no stream_settings for Reality
                    return {}
            
            outbound["tls"] = tls_config
        
        # Add transport settings
        if inbound.network and inbound.network != "tcp":
            transport = {"type": inbound.network}
            
            # Add WebSocket path and headers if present
            if inbound.network == "ws" and inbound.stream_settings:
                ws_settings = inbound.stream_settings.get("ws", {})
                if ws_settings.get("path"):
                    transport["path"] = ws_settings["path"]
                # Add Host header for WebSocket (important for CDN)
                transport["headers"] = {
                    "Host": proxy.sni or server
                }
            
            outbound["transport"] = transport
        
        return outbound
    
    elif proxy.type == "VMESS" and proxy.vmess_uuid:
        outbound = {
            "type": "vmess",
            "tag": tag,
            "server": server,
            "server_port": inbound.port,
            "uuid": proxy.vmess_uuid,
            "security": "auto",
            "authenticated_length": True,
            "packet_encoding": "xudp"
        }
        
        # Add TLS settings
        if inbound.security == "tls":
            tls_config = {
                "enabled": True,
                "server_name": proxy.sni or server
            }
            
            # Add ALPN if present
            if proxy.alpn:
                tls_config["alpn"] = proxy.alpn[0] if len(proxy.alpn) == 1 else proxy.alpn
            
            # Add uTLS without disable_sni
            if proxy.fingerprint:
                tls_config["utls"] = {
                    "enabled": True,
                    "fingerprint": proxy.fingerprint
                }
            
            outbound["tls"] = tls_config
        
        # Add transport settings
        if inbound.network and inbound.network != "tcp":
            transport = {"type": inbound.network}
            
            if inbound.network == "grpc":
                transport["idle_timeout"] = "15s"
                transport["ping_timeout"] = "15s"
                # Add gRPC service name
                if inbound.stream_settings:
                    grpc_settings = inbound.stream_settings.get("grpc", {})
                    if grpc_settings.get("serviceName"):
                        transport["service_name"] = grpc_settings["serviceName"]
            
            elif inbound.network == "ws" and inbound.stream_settings:
                ws_settings = inbound.stream_settings.get("ws", {})
                if ws_settings.get("path"):
                    transport["path"] = ws_settings["path"]
                # Add Host header for WebSocket
                transport["headers"] = {
                    "Host": proxy.sni or server
                }
            
            outbound["transport"] = transport
        
        return outbound
    
    elif proxy.type == "SHADOWSOCKS" and proxy.ss_password:
        return {
            "type": "shadowsocks",
            "tag": tag,
            "server": server,
            "server_port": inbound.port,
            "method": proxy.ss_method or "aes-256-gcm",
            "password": proxy.ss_password
        }
    
    elif proxy.type == "HYSTERIA" and proxy.hysteria_password:
        # Hysteria v1 is deprecated, skip it
        return {}
    
    elif proxy.type == "HYSTERIA2" and proxy.hysteria2_password:
        return {
            "type": "hysteria2",
            "tag": tag,
            "server": server,
            "server_port": inbound.port,
            "password": proxy.vmess_uuid or proxy.hysteria2_password,
            "tls": {
                "enabled": True,
                "server_name": proxy.sni or server,
                "insecure": True
            }
        }
    
    return {}


@router.get("/singbox/{token}")
async def get_singbox_subscription(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get sing-box JSON subscription by token"""
    # Load user with proxies by subscription_token
    result = await db.execute(
        select(User)
        .options(selectinload(User.proxies))
        .where(User.subscription_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    if user.sub_revoked_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription has been revoked",
        )
    
    # Get user's inbound tags
    result = await db.execute(
        select(UserInbound.inbound_tag)
        .where(UserInbound.user_id == user.id)
    )
    inbound_tags = [row[0] for row in result.all()]
    
    if not inbound_tags:
        return Response(content=json.dumps({"outbounds": []}), media_type="application/json")
    
    # Get username tag from settings
    username_tag = ""
    tag_setting = await db.execute(
        select(Settings).where(Settings.key == "username_tag")
    )
    tag_setting = tag_setting.scalar_one_or_none()
    if tag_setting and tag_setting.value:
        username_tag = f" {tag_setting.value}"
    
    # Get inbounds
    result = await db.execute(
        select(Inbound)
        .where(Inbound.tag.in_(inbound_tags))
        .where(Inbound.is_enabled == True)
    )
    inbounds = result.scalars().all()
    
    if not inbounds:
        return Response(content=json.dumps({"outbounds": []}), media_type="application/json")
    
    # Generate sing-box outbounds
    outbounds = []
    server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
    idx = 0
    
    for proxy in user.proxies:
        for inbound in inbounds:
            # Match proxy type with inbound type
            proxy_type_map = {
                "VLESS": "vless",
                "VMESS": "vmess",
                "TROJAN": "trojan",
                "SHADOWSOCKS": "shadowsocks",
                "HYSTERIA": "hysteria",
                "HYSTERIA2": "hysteria2"
            }
            
            if proxy.type.upper() not in proxy_type_map:
                continue
                
            if proxy_type_map[proxy.type.upper()] != inbound.type.lower():
                continue
            
            outbound = generate_singbox_outbound(proxy, inbound, server, username_tag, idx)
            if outbound:
                outbounds.append(outbound)
                idx += 1
    
    config = {"outbounds": outbounds}
    return Response(content=json.dumps(config, indent=2, ensure_ascii=False), media_type="application/json")
