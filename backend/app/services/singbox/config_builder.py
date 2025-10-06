"""
Sing-box configuration builder for Hysteria/Hysteria2 protocols
"""
import json
from typing import Dict, List, Any


class SingBoxConfigBuilder:
    """Build sing-box configuration for Hysteria protocols"""
    
    def __init__(self):
        self.config = {
            "log": {
                "level": "warn",
                "timestamp": True
            },
            "inbounds": [],
            "outbounds": [
                {
                    "type": "direct",
                    "tag": "direct"
                }
            ]
        }
    
    def add_hysteria_inbound(
        self,
        inbound: Any,
        users: List[Dict[str, Any]]
    ) -> None:
        """Add Hysteria inbound configuration"""
        hysteria_users = []
        
        for user_data in users:
            # Find Hysteria proxy for this user
            for proxy in user_data.get("proxies", []):
                if proxy.get("type") == "HYSTERIA":
                    hysteria_users.append({
                        "name": user_data.get("email", ""),
                        "auth": proxy.get("password", "")
                    })
                    break
        
        hysteria_inbound = {
            "type": "hysteria",
            "tag": inbound.tag,
            "listen": inbound.listen,
            "listen_port": inbound.port,
            "up_mbps": 100,
            "down_mbps": 100,
            "users": hysteria_users,
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True
            }
        }
        
        self.config["inbounds"].append(hysteria_inbound)
    
    def add_hysteria2_inbound(
        self,
        inbound: Any,
        users: List[Dict[str, Any]]
    ) -> None:
        """Add Hysteria2 inbound configuration"""
        hysteria2_users = []
        
        for user_data in users:
            # Find Hysteria2 proxy for this user
            for proxy in user_data.get("proxies", []):
                if proxy.get("type") == "HYSTERIA2":
                    hysteria2_users.append({
                        "name": user_data.get("email", ""),
                        "password": proxy.get("password", "")
                    })
                    break
        
        hysteria2_inbound = {
            "type": "hysteria2",
            "tag": inbound.tag,
            "listen": inbound.listen,
            "listen_port": inbound.port,
            "up_mbps": 100,
            "down_mbps": 100,
            "users": hysteria2_users,
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True,
                "alpn": ["h3"]
            }
        }
        
        self.config["inbounds"].append(hysteria2_inbound)
    
    def build(self) -> str:
        """Build and return JSON configuration"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)
