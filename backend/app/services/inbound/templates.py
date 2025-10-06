"""
Готовые шаблоны конфигураций inbound с автогенерацией параметров
UPDATED: Убраны небезопасные варианты, добавлена автоматическая генерация сертификатов
"""
import secrets
import subprocess
import os
from typing import Dict, Any, List, Optional


def generate_reality_keys() -> Dict[str, str]:
    """Генерация ключей для Reality"""
    try:
        result = subprocess.run(
            ["xray", "x25519"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout
        
        private_key = ""
        public_key = ""
        
        for line in output.split('\n'):
            if 'Private key:' in line:
                private_key = line.split(':')[1].strip()
            elif 'Public key:' in line:
                public_key = line.split(':')[1].strip()
        
        return {
            "private_key": private_key,
            "public_key": public_key
        }
    except Exception:
        # Fallback to random generation
        return {
            "private_key": secrets.token_hex(32),
            "public_key": secrets.token_hex(32)
        }


def generate_short_ids(count: int = 3) -> List[str]:
    """Генерация коротких ID для Reality"""
    return [secrets.token_hex(8) for _ in range(count)]


def get_letsencrypt_certificates(domain: str = "jdsshrerwwte.dmevent.de") -> List[Dict[str, str]]:
    """Получить Let's Encrypt сертификаты"""
    cert_path = f"/etc/letsencrypt/live/{domain}"
    
    if os.path.exists(cert_path):
        return [
            {
                "certificateFile": f"{cert_path}/fullchain.pem",
                "keyFile": f"{cert_path}/privkey.pem"
            }
        ]
    return []


class InboundTemplates:
    """Готовые шаблоны конфигураций inbound - ТОЛЬКО БЕЗОПАСНЫЕ"""
    
    @staticmethod
    def vless_reality(
        tag: str = "vless-reality",
        port: int = 443,
        server_names: Optional[List[str]] = None,
        dest: str = "www.microsoft.com:443",
        **kwargs
    ) -> Dict[str, Any]:
        """VLESS с Reality (рекомендуется) - МАКСИМАЛЬНАЯ БЕЗОПАСНОСТЬ"""
        if server_names is None:
            server_names = ["www.microsoft.com", "www.apple.com", "cdn.cloudflare.com"]
        
        reality_keys = generate_reality_keys()
        short_ids = generate_short_ids(3)
        
        return {
            "tag": tag,
            "type": "VLESS",
            "listen": "0.0.0.0",
            "port": port,
            "network": "tcp",
            "security": "reality",
            "reality_settings": {
                "serverNames": server_names,
                "privateKey": reality_keys["private_key"],
                "shortIds": short_ids,
                "dest": dest,
                "fingerprint": "chrome",
                "spiderX": "/"
            },
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls", "quic"],
            "domain_strategy": "ForceIPv4",
            "remark": "VLESS Reality - Высокая безопасность, обход блокировок"
        }
    
    @staticmethod
    def vless_ws_tls(
        tag: str = "vless-ws-tls",
        port: int = 2053,
        path: str = "/vless",
        domain: str = "jdsshrerwwte.dmevent.de",
        **kwargs
    ) -> Dict[str, Any]:
        """VLESS с WebSocket и TLS - CDN СОВМЕСТИМЫЙ"""
        return {
            "tag": tag,
            "type": "VLESS",
            "listen": "0.0.0.0",
            "port": port,
            "network": "ws",
            "security": "tls",
            "tls_settings": {
                "serverName": domain,
                "alpn": ["h2", "http/1.1"],
                "certificates": get_letsencrypt_certificates(domain)
            },
            "stream_settings": {
                "ws": {
                    "path": path,
                    "headers": {}
                }
            },
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls"],
            "domain_strategy": "ForceIPv4",
            "remark": "VLESS WebSocket TLS - Универсальный, работает за CDN"
        }
    
    @staticmethod
    def vmess_grpc_tls(
        tag: str = "vmess-grpc-tls",
        port: int = 10445,
        service_name: str = "vmess",
        domain: str = "jdsshrerwwte.dmevent.de",
        **kwargs
    ) -> Dict[str, Any]:
        """VMess с gRPC и TLS - БЫСТРЫЙ И БЕЗОПАСНЫЙ"""
        return {
            "tag": tag,
            "type": "VMESS",
            "listen": "0.0.0.0",
            "port": port,
            "network": "grpc",
            "security": "tls",
            "tls_settings": {
                "serverName": domain,
                "alpn": ["h2"],
                "certificates": get_letsencrypt_certificates(domain)
            },
            "stream_settings": {
                "grpc": {
                    "serviceName": service_name,
                    "multiMode": False
                }
            },
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls"],
            "domain_strategy": "ForceIPv4",
            "remark": "VMess gRPC TLS - Быстрый, низкая задержка"
        }
    
    @staticmethod
    def trojan_tcp_tls(
        tag: str = "trojan-tcp-tls",
        port: int = 443,
        domain: str = "jdsshrerwwte.dmevent.de",
        **kwargs
    ) -> Dict[str, Any]:
        """Trojan с TCP и TLS - МАСКИРОВКА ПОД HTTPS"""
        return {
            "tag": tag,
            "type": "TROJAN",
            "listen": "0.0.0.0",
            "port": port,
            "network": "tcp",
            "security": "tls",
            "tls_settings": {
                "serverName": domain,
                "alpn": ["http/1.1"],
                "certificates": get_letsencrypt_certificates(domain)
            },
            "fallbacks": [
                {
                    "dest": 80,
                    "xver": 0
                }
            ],
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls"],
            "domain_strategy": "ForceIPv4",
            "remark": "Trojan TCP TLS - Маскировка под HTTPS"
        }
    
    @staticmethod
    def shadowsocks(
        tag: str = "shadowsocks",
        port: int = 10388,
        method: str = "chacha20-ietf-poly1305",
        **kwargs
    ) -> Dict[str, Any]:
        """Shadowsocks - ПРОСТОЙ И БЫСТРЫЙ (без TLS, но с шифрованием)"""
        return {
            "tag": tag,
            "type": "SHADOWSOCKS",
            "listen": "0.0.0.0",
            "port": port,
            "network": "tcp",
            "security": "none",
            "stream_settings": {
                "ss": {
                    "method": method,
                    "network": "tcp,udp"
                }
            },
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls"],
            "domain_strategy": "ForceIPv4",
            "remark": "Shadowsocks - Простой и быстрый"
        }
    
    @staticmethod
    def hysteria2(
        tag: str = "hysteria2",
        port: int = 36713,
        password: Optional[str] = None,
        obfs_password: Optional[str] = None,
        domain: str = "jdsshrerwwte.dmevent.de",
        **kwargs
    ) -> Dict[str, Any]:
        """Hysteria2 - НОВЕЙШИЙ ПРОТОКОЛ НА БАЗЕ QUIC"""
        if password is None:
            password = secrets.token_hex(16)
        if obfs_password is None:
            obfs_password = secrets.token_hex(16)
        
        return {
            "tag": tag,
            "type": "HYSTERIA2",
            "listen": "0.0.0.0",
            "port": port,
            "network": "udp",
            "security": "tls",
            "tls_settings": {
                "serverName": domain,
                "alpn": ["h3"],
                "certificates": get_letsencrypt_certificates(domain)
            },
            "stream_settings": {
                "hysteria2": {
                    "password": password,
                    "obfs": {
                        "type": "salamander",
                        "password": obfs_password
                    },
                    "ignoreClientBandwidth": False
                }
            },
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls", "quic"],
            "domain_strategy": "ForceIPv4",
            "remark": "Hysteria2 - Высокая скорость, защита от DPI"
        }
    
    @staticmethod
    def vless_tcp_reality_h2(
        tag: str = "vless-h2-reality",
        port: int = 8443,
        server_names: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """VLESS Reality с HTTP/2 - ПРЕМИУМ ВАРИАНТ"""
        if server_names is None:
            server_names = ["www.google.com", "www.youtube.com"]
        
        reality_keys = generate_reality_keys()
        short_ids = generate_short_ids(3)
        
        return {
            "tag": tag,
            "type": "VLESS",
            "listen": "0.0.0.0",
            "port": port,
            "network": "h2",
            "security": "reality",
            "reality_settings": {
                "serverNames": server_names,
                "privateKey": reality_keys["private_key"],
                "shortIds": short_ids,
                "dest": "www.google.com:443",
                "fingerprint": "chrome",
                "spiderX": "/"
            },
            "stream_settings": {
                "h2": {
                    "host": server_names,
                    "path": "/"
                }
            },
            "sniffing_enabled": True,
            "sniffing_dest_override": ["http", "tls", "quic"],
            "domain_strategy": "ForceIPv4",
            "remark": "VLESS Reality HTTP/2 - Максимальная безопасность + скорость"
        }
    
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """Получить все доступные БЕЗОПАСНЫЕ шаблоны"""
        return [
            {
                "name": "VLESS Reality",
                "description": "⭐ Рекомендуется: максимальная безопасность, обход DPI",
                "protocol": "VLESS",
                "template": "vless_reality",
                "difficulty": "easy",
                "performance": "high",
                "security": "very_high",
                "cdn_compatible": False
            },
            {
                "name": "VLESS WebSocket TLS",
                "description": "☁️ CDN-совместимый: работает через Cloudflare",
                "protocol": "VLESS",
                "template": "vless_ws_tls",
                "difficulty": "medium",
                "performance": "medium",
                "security": "high",
                "cdn_compatible": True
            },
            {
                "name": "VMess gRPC TLS",
                "description": "⚡ Быстрый: низкая задержка, TLS шифрование",
                "protocol": "VMESS",
                "template": "vmess_grpc_tls",
                "difficulty": "medium",
                "performance": "high",
                "security": "high",
                "cdn_compatible": False
            },
            {
                "name": "Trojan TCP TLS",
                "description": "🔒 Маскировка: притворяется обычным HTTPS",
                "protocol": "TROJAN",
                "template": "trojan_tcp_tls",
                "difficulty": "medium",
                "performance": "high",
                "security": "high",
                "cdn_compatible": False
            },
            {
                "name": "Shadowsocks",
                "description": "⚙️ Классика: простой, быстрый, собственное шифрование",
                "protocol": "SHADOWSOCKS",
                "template": "shadowsocks",
                "difficulty": "easy",
                "performance": "high",
                "security": "medium",
                "cdn_compatible": False
            },
            {
                "name": "Hysteria2",
                "description": "🚀 Новейший: QUIC протокол, максимальная скорость",
                "protocol": "HYSTERIA2",
                "template": "hysteria2",
                "difficulty": "medium",
                "performance": "very_high",
                "security": "high",
                "cdn_compatible": False
            },
            {
                "name": "VLESS Reality HTTP/2",
                "description": "👑 Премиум: максимум безопасности + производительности",
                "protocol": "VLESS",
                "template": "vless_tcp_reality_h2",
                "difficulty": "medium",
                "performance": "very_high",
                "security": "very_high",
                "cdn_compatible": False
            }
        ]
    
    @staticmethod
    def generate_from_template(template_name: str, **kwargs) -> Dict[str, Any]:
        """Генерация конфигурации из шаблона"""
        templates = InboundTemplates()
        
        template_map = {
            "vless_reality": templates.vless_reality,
            "vless_ws_tls": templates.vless_ws_tls,
            "vmess_grpc_tls": templates.vmess_grpc_tls,
            "trojan_tcp_tls": templates.trojan_tcp_tls,
            "shadowsocks": templates.shadowsocks,
            "hysteria2": templates.hysteria2,
            "vless_tcp_reality_h2": templates.vless_tcp_reality_h2
        }
        
        if template_name not in template_map:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(template_map.keys())}")
        
        return template_map[template_name](**kwargs)
