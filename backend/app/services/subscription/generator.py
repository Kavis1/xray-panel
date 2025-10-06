import base64
import json
import yaml
from typing import List, Dict, Any
from urllib.parse import quote
from app.models.user import User
from app.core.config import settings


class SubscriptionGenerator:
    """Generate subscription links for various clients"""

    def __init__(self, user: User):
        self.user = user

    def generate_v2ray(self) -> str:
        """Generate V2Ray subscription (base64 encoded links)"""
        links = []
        
        for proxy in self.user.proxies:
            if proxy.type == "VLESS":
                link = self._generate_vless_link(proxy)
            elif proxy.type == "VMESS":
                link = self._generate_vmess_link(proxy)
            elif proxy.type == "TROJAN":
                link = self._generate_trojan_link(proxy)
            elif proxy.type == "SHADOWSOCKS":
                link = self._generate_ss_link(proxy)
            else:
                continue
            
            if link:
                links.append(link)
        
        content = "\n".join(links)
        return base64.b64encode(content.encode()).decode()

    def generate_clash(self) -> str:
        """Generate Clash YAML configuration"""
        proxies = []
        proxy_names = []

        for idx, proxy in enumerate(self.user.proxies):
            proxy_config = self._generate_clash_proxy(proxy, idx)
            if proxy_config:
                proxies.append(proxy_config)
                proxy_names.append(proxy_config["name"])

        config = {
            "port": 7890,
            "socks-port": 7891,
            "allow-lan": False,
            "mode": "rule",
            "log-level": "info",
            "external-controller": "127.0.0.1:9090",
            "proxies": proxies,
            "proxy-groups": [
                {
                    "name": "PROXY",
                    "type": "select",
                    "proxies": proxy_names
                }
            ],
            "rules": [
                "MATCH,PROXY"
            ]
        }

        return yaml.dump(config, allow_unicode=True, default_flow_style=False)

    def generate_singbox(self) -> str:
        """Generate Sing-box JSON configuration"""
        outbounds = []

        for idx, proxy in enumerate(self.user.proxies):
            outbound = self._generate_singbox_outbound(proxy, idx)
            if outbound:
                outbounds.append(outbound)

        config = {
            "log": {
                "level": "info"
            },
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 2080
                }
            ],
            "outbounds": outbounds + [
                {
                    "type": "direct",
                    "tag": "direct"
                },
                {
                    "type": "block",
                    "tag": "block"
                }
            ],
            "route": {
                "rules": []
            }
        }

        return json.dumps(config, indent=2)

    def _generate_vless_link(self, proxy) -> str:
        """Generate VLESS link"""
        params = {
            "type": proxy.network or "tcp",
            "security": proxy.security or "none",
        }

        if proxy.sni:
            params["sni"] = proxy.sni
        if proxy.alpn:
            params["alpn"] = ",".join(proxy.alpn)
        if proxy.fingerprint:
            params["fp"] = proxy.fingerprint
        if proxy.vless_flow:
            params["flow"] = proxy.vless_flow

        query = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        
        server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
        port = 443

        return f"vless://{proxy.vless_uuid}@{server}:{port}?{query}#{quote(self.user.username)}"

    def _generate_vmess_link(self, proxy) -> str:
        """Generate VMess link"""
        server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
        
        config = {
            "v": "2",
            "ps": self.user.username,
            "add": server,
            "port": 443,
            "id": proxy.vmess_uuid,
            "aid": 0,
            "net": proxy.network or "tcp",
            "type": "none",
            "host": "",
            "path": "",
            "tls": proxy.security or "none",
            "sni": proxy.sni or "",
            "alpn": ",".join(proxy.alpn) if proxy.alpn else ""
        }

        json_str = json.dumps(config)
        encoded = base64.b64encode(json_str.encode()).decode()
        return f"vmess://{encoded}"

    def _generate_trojan_link(self, proxy) -> str:
        """Generate Trojan link"""
        server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
        port = 443

        params = {}
        if proxy.sni:
            params["sni"] = proxy.sni
        if proxy.alpn:
            params["alpn"] = ",".join(proxy.alpn)
        if proxy.fingerprint:
            params["fp"] = proxy.fingerprint

        query = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        query_str = f"?{query}" if query else ""

        return f"trojan://{proxy.trojan_password}@{server}:{port}{query_str}#{quote(self.user.username)}"

    def _generate_ss_link(self, proxy) -> str:
        """Generate Shadowsocks link"""
        server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
        port = 443

        method = proxy.ss_method or "chacha20-poly1305"
        password = proxy.ss_password

        userinfo = f"{method}:{password}"
        encoded = base64.b64encode(userinfo.encode()).decode()

        return f"ss://{encoded}@{server}:{port}#{quote(self.user.username)}"

    def _generate_clash_proxy(self, proxy, idx: int) -> Dict[str, Any]:
        """Generate Clash proxy configuration"""
        server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
        name = f"{self.user.username}-{idx}"

        if proxy.type == "VLESS":
            return {
                "name": name,
                "type": "vless",
                "server": server,
                "port": 443,
                "uuid": proxy.vless_uuid,
                "network": proxy.network or "tcp",
                "tls": proxy.security == "tls",
                "skip-cert-verify": False
            }
        elif proxy.type == "VMESS":
            return {
                "name": name,
                "type": "vmess",
                "server": server,
                "port": 443,
                "uuid": proxy.vmess_uuid,
                "alterId": 0,
                "cipher": "auto",
                "network": proxy.network or "tcp",
                "tls": proxy.security == "tls"
            }
        elif proxy.type == "TROJAN":
            return {
                "name": name,
                "type": "trojan",
                "server": server,
                "port": 443,
                "password": proxy.trojan_password,
                "skip-cert-verify": False
            }
        elif proxy.type == "SHADOWSOCKS":
            return {
                "name": name,
                "type": "ss",
                "server": server,
                "port": 443,
                "cipher": proxy.ss_method or "chacha20-poly1305",
                "password": proxy.ss_password
            }

        return {}

    def _generate_singbox_outbound(self, proxy, idx: int) -> Dict[str, Any]:
        """Generate Sing-box outbound configuration"""
        server = settings.XRAY_SUBSCRIPTION_URL_PREFIX.split("//")[1].split("/")[0]
        tag = f"{self.user.username}-{idx}"

        if proxy.type == "VLESS":
            return {
                "type": "vless",
                "tag": tag,
                "server": server,
                "server_port": 443,
                "uuid": proxy.vless_uuid,
                "flow": proxy.vless_flow or "",
                "network": proxy.network or "tcp",
                "tls": {
                    "enabled": proxy.security == "tls",
                    "server_name": proxy.sni or server
                }
            }
        elif proxy.type == "VMESS":
            return {
                "type": "vmess",
                "tag": tag,
                "server": server,
                "server_port": 443,
                "uuid": proxy.vmess_uuid,
                "security": "auto",
                "alter_id": 0,
                "network": proxy.network or "tcp",
                "tls": {
                    "enabled": proxy.security == "tls",
                    "server_name": proxy.sni or server
                }
            }
        elif proxy.type == "TROJAN":
            return {
                "type": "trojan",
                "tag": tag,
                "server": server,
                "server_port": 443,
                "password": proxy.trojan_password,
                "tls": {
                    "enabled": True,
                    "server_name": proxy.sni or server
                }
            }
        elif proxy.type == "SHADOWSOCKS":
            return {
                "type": "shadowsocks",
                "tag": tag,
                "server": server,
                "server_port": 443,
                "method": proxy.ss_method or "chacha20-poly1305",
                "password": proxy.ss_password
            }

        return {}
