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
        users: List[Any]  # List of User objects with proxies
    ) -> None:
        """Add Hysteria inbound configuration"""
        hysteria_users = []
        
        for user in users:
            # Find Hysteria proxy for this user
            for proxy in user.proxies:
                if proxy.type.upper() == "HYSTERIA" and proxy.vmess_uuid:
                    # Hysteria uses auth_str (not base64)
                    hysteria_users.append({
                        "name": user.username,
                        "auth_str": proxy.vmess_uuid
                    })
                    break
        
        # TLS certificate paths
        tls_config = {
            "enabled": True,
            "server_name": "jdsshrerwwte.dmevent.de",
            "certificate_path": "/etc/letsencrypt/live/jdsshrerwwte.dmevent.de/fullchain.pem",
            "key_path": "/etc/letsencrypt/live/jdsshrerwwte.dmevent.de/privkey.pem"
        }
        
        hysteria_inbound = {
            "type": "hysteria",
            "tag": inbound.tag,
            "listen": inbound.listen or "0.0.0.0",
            "listen_port": inbound.port,
            "up_mbps": 100,
            "down_mbps": 100,
            "users": hysteria_users,
            "tls": tls_config
        }
        
        self.config["inbounds"].append(hysteria_inbound)
    
    def add_hysteria2_inbound(
        self,
        inbound: Any,
        users: List[Any],  # List of User objects with proxies
        node_domain: str = None  # Node's domain for TLS cert
    ) -> None:
        """Add Hysteria2 inbound configuration"""
        hysteria2_users = []
        
        for user in users:
            # Find Hysteria2 proxy for this user
            for proxy in user.proxies:
                if proxy.type.upper() == "HYSTERIA2" and proxy.vmess_uuid:
                    hysteria2_users.append({
                        "name": user.username,
                        "password": proxy.vmess_uuid  # Hysteria2 uses UUID as password
                    })
                    break
        
        # Use node's domain for certificate path, fallback to main domain
        cert_domain = node_domain or "jdsshrerwwte.dmevent.de"
        
        # TLS certificate paths
        tls_config = {
            "enabled": True,
            "server_name": cert_domain,
            "certificate_path": f"/etc/letsencrypt/live/{cert_domain}/fullchain.pem",
            "key_path": f"/etc/letsencrypt/live/{cert_domain}/privkey.pem",
            "alpn": ["h3"]
        }
        
        hysteria2_inbound = {
            "type": "hysteria2",
            "tag": inbound.tag,
            "listen": inbound.listen or "0.0.0.0",
            "listen_port": inbound.port,
            "up_mbps": 100,
            "down_mbps": 100,
            "users": hysteria2_users,
            "tls": tls_config
        }
        
        self.config["inbounds"].append(hysteria2_inbound)
    
    def build(self) -> str:
        """Build and return JSON configuration"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)
