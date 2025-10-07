import json
from typing import List, Dict, Any
from app.models.inbound import Inbound
from app.models.user import User


class XrayConfigBuilder:
    def __init__(self):
        self.config: Dict[str, Any] = {
            "log": {
                "loglevel": "warning"
            },
            "api": {
                "tag": "api",
                "services": ["StatsService"]
            },
            "stats": {},
            "policy": {
                "levels": {
                    "0": {
                        "statsUserUplink": True,
                        "statsUserDownlink": True
                    }
                },
                "system": {
                    "statsInboundUplink": True,
                    "statsInboundDownlink": True,
                    "statsOutboundUplink": True,
                    "statsOutboundDownlink": True
                }
            },
            "inbounds": [],
            "outbounds": [
                {
                    "tag": "direct",
                    "protocol": "freedom",
                    "settings": {
                        "domainStrategy": "ForceIPv4"
                    }
                },
                {
                    "tag": "block",
                    "protocol": "blackhole",
                    "settings": {}
                }
            ],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": []
            },
            "blocked_protocols": []  # Will be populated with inbound tags that block torrents
        }
    
    def add_torrent_blocking_rules(self, inbound_tags: List[str]) -> None:
        """Add routing rules to block BitTorrent traffic for specific inbounds"""
        if not inbound_tags:
            return
        
        # Block BitTorrent protocol
        torrent_rule = {
            "type": "field",
            "inboundTag": inbound_tags,
            "protocol": ["bittorrent"],
            "outboundTag": "block"
        }
        
        self.config["routing"]["rules"].insert(0, torrent_rule)
        
    def finalize_routing(self) -> None:
        """Finalize routing rules by adding API route at the end"""
        # Add API routing rule (must be last)
        api_rule = {
            "type": "field",
            "inboundTag": ["api"],
            "outboundTag": "api"
        }
        self.config["routing"]["rules"].append(api_rule)

    def add_inbound(self, inbound: Inbound, users: List[User]) -> None:
        """Add inbound configuration with users"""
        # Skip Hysteria protocols - they are handled by sing-box
        if inbound.type in ["HYSTERIA", "HYSTERIA2"]:
            return
        
        inbound_config = {
            "tag": inbound.tag,
            "listen": inbound.listen,
            "port": inbound.port,
            "protocol": self._get_protocol_name(inbound.type),
            "settings": self._build_inbound_settings(inbound, users),
            "streamSettings": self._build_stream_settings(inbound),
        }

        if inbound.sniffing_enabled:
            inbound_config["sniffing"] = {
                "enabled": True,
                "destOverride": inbound.sniffing_dest_override or ["http", "tls"],
                "domainStrategy": inbound.domain_strategy or "ForceIPv4"
            }

        self.config["inbounds"].append(inbound_config)

    def _get_protocol_name(self, protocol_type: str) -> str:
        """Convert protocol type to Xray protocol name"""
        mapping = {
            "VLESS": "vless",
            "VMESS": "vmess",
            "TROJAN": "trojan",
            "SHADOWSOCKS": "shadowsocks"
        }
        return mapping.get(protocol_type.upper(), protocol_type.lower())

    def _build_inbound_settings(self, inbound: Inbound, users: List[User]) -> Dict[str, Any]:
        """Build protocol-specific settings with clients"""
        clients = []

        for user in users:
            for proxy in user.proxies:
                if proxy.type.upper() == inbound.type.upper():
                    client = self._build_client(user, proxy, inbound)
                    if client:
                        clients.append(client)

        settings: Dict[str, Any] = {
            "clients": clients
        }

        if inbound.type.upper() == "VLESS":
            settings["decryption"] = "none"
        elif inbound.type.upper() == "SHADOWSOCKS":
            settings["method"] = "chacha20-poly1305"
            settings["network"] = "tcp,udp"

        return settings

    def _build_client(self, user: User, proxy, inbound: Inbound) -> Dict[str, Any]:
        """Build client configuration based on protocol"""
        protocol = proxy.type.upper()

        if protocol == "VLESS":
            client_config = {
                "id": proxy.vless_uuid,
                "email": user.email or user.username,
                "level": 0
            }
            # Add flow ONLY for Reality (not for regular TLS)
            if proxy.vless_flow and inbound.security == "reality":
                client_config["flow"] = proxy.vless_flow
            return client_config
        elif protocol == "VMESS":
            return {
                "id": proxy.vmess_uuid,
                "email": user.email or user.username,
                "level": 0,
                "alterId": 0
            }
        elif protocol == "TROJAN":
            return {
                "password": proxy.trojan_password,
                "email": user.email or user.username,
                "level": 0
            }
        elif protocol == "SHADOWSOCKS":
            return {
                "password": proxy.ss_password,
                "email": user.email or user.username,
                "method": proxy.ss_method or "chacha20-poly1305",
                "level": 0
            }

        return {}

    def _build_stream_settings(self, inbound: Inbound) -> Dict[str, Any]:
        """Build stream settings (transport, security)"""
        stream_settings = {
            "network": inbound.network
        }

        # Check if stream_settings has security configuration
        if inbound.stream_settings:
            # Reality Settings from stream_settings
            if inbound.security == "reality" and "reality_settings" in inbound.stream_settings:
                stream_settings["security"] = "reality"
                reality_cfg = inbound.stream_settings["reality_settings"]
                stream_settings["realitySettings"] = {
                    "show": False,
                    "dest": reality_cfg.get("dest", "www.microsoft.com:443"),
                    "serverNames": reality_cfg.get("serverNames", ["www.microsoft.com"]),
                    "privateKey": reality_cfg.get("privateKey", ""),
                    "shortIds": reality_cfg.get("shortIds", [])
                }
                if "spiderX" in reality_cfg:
                    stream_settings["realitySettings"]["spiderX"] = reality_cfg["spiderX"]
            # TLS Settings from stream_settings
            elif inbound.security == "tls" and "tls_settings" in inbound.stream_settings:
                stream_settings["security"] = "tls"
                stream_settings["tlsSettings"] = inbound.stream_settings["tls_settings"]
            
            # Transport specific settings
            if inbound.network == "ws":
                if "wsSettings" in inbound.stream_settings:
                    stream_settings["wsSettings"] = inbound.stream_settings["wsSettings"]
                elif "ws" in inbound.stream_settings:
                    stream_settings["wsSettings"] = inbound.stream_settings["ws"]
            elif inbound.network == "grpc":
                if "grpcSettings" in inbound.stream_settings:
                    stream_settings["grpcSettings"] = inbound.stream_settings["grpcSettings"]
                elif "grpc" in inbound.stream_settings:
                    stream_settings["grpcSettings"] = inbound.stream_settings["grpc"]
            elif inbound.network == "h2":
                if "httpSettings" in inbound.stream_settings:
                    stream_settings["httpSettings"] = inbound.stream_settings["httpSettings"]
                elif "h2" in inbound.stream_settings:
                    stream_settings["httpSettings"] = inbound.stream_settings["h2"]
            elif inbound.network == "quic":
                if "quicSettings" in inbound.stream_settings:
                    stream_settings["quicSettings"] = inbound.stream_settings["quicSettings"]
                elif "quic" in inbound.stream_settings:
                    stream_settings["quicSettings"] = inbound.stream_settings["quic"]
            
            # Add default TLS if security is tls but not yet added
            if inbound.security == "tls" and "security" not in stream_settings:
                stream_settings["security"] = "tls"
                stream_settings["tlsSettings"] = {
                    "serverName": "",
                    "alpn": ["http/1.1"],
                    "certificates": []
                }
        # Fallback: check direct fields
        elif inbound.security == "tls":
            stream_settings["security"] = "tls"
            if inbound.tls_settings:
                stream_settings["tlsSettings"] = inbound.tls_settings
            else:
                # Default TLS settings
                stream_settings["tlsSettings"] = {
                    "serverName": "",
                    "alpn": ["http/1.1"],
                    "certificates": []
                }
        elif inbound.security == "reality" and inbound.reality_settings:
            stream_settings["security"] = "reality"
            reality_cfg = inbound.reality_settings
            stream_settings["realitySettings"] = {
                "show": False,
                "dest": reality_cfg.get("dest", "www.microsoft.com:443"),
                "serverNames": reality_cfg.get("serverNames", ["www.microsoft.com"]),
                "privateKey": reality_cfg.get("privateKey", ""),
                "shortIds": reality_cfg.get("shortIds", [])
            }
            if "fingerprint" in reality_cfg:
                stream_settings["realitySettings"]["fingerprint"] = reality_cfg["fingerprint"]
            if "spiderX" in reality_cfg:
                stream_settings["realitySettings"]["spiderX"] = reality_cfg["spiderX"]

        return stream_settings

    def add_api_inbound(self, port: int = 10085) -> None:
        """Add API inbound for statistics"""
        api_inbound = {
            "tag": "api",
            "listen": "127.0.0.1",
            "port": port,
            "protocol": "dokodemo-door",
            "settings": {
                "address": "127.0.0.1"
            }
        }
        self.config["inbounds"].insert(0, api_inbound)

    def build(self) -> str:
        """Build and return final JSON configuration"""
        # Finalize routing before building
        self.finalize_routing()
        
        # Remove helper field
        if "blocked_protocols" in self.config:
            del self.config["blocked_protocols"]
        
        return json.dumps(self.config, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        # Finalize routing
        self.finalize_routing()
        
        # Remove helper field
        if "blocked_protocols" in self.config:
            del self.config["blocked_protocols"]
        
        return self.config
