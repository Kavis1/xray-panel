"""
Node and Inbound compatibility checker
"""
import re
from typing import Optional


def is_domain(address: str) -> bool:
    """Check if address is a domain name (not IP)"""
    # Simple IP check (IPv4)
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, address):
        return False
    
    # Check for IPv6
    if ':' in address and not '.' in address:
        return False
    
    # If contains letters and dots, likely a domain
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', address))


def node_supports_tls(node_address: str, node_domain: Optional[str] = None) -> bool:
    """
    Check if node supports TLS-based protocols
    
    TLS requires:
    - Valid domain name (not IP)
    - SSL certificate
    
    Returns True if node has domain, False if only IP
    """
    # If node has explicit domain, it supports TLS
    if node_domain:
        return is_domain(node_domain)
    
    # Check if address itself is a domain
    return is_domain(node_address)


def inbound_requires_tls(inbound_type: str, security: Optional[str] = None) -> bool:
    """
    Check if inbound requires TLS certificate
    
    Protocols that REQUIRE TLS:
    - Trojan (always)
    - VLESS with Reality
    - VMess with TLS
    - Hysteria/Hysteria2 (need valid cert for proper TLS)
    - Any protocol with security='tls' or 'reality'
    
    Protocols that DON'T require TLS:
    - VMess without TLS
    - VLESS without TLS/Reality
    - Shadowsocks
    """
    inbound_type = inbound_type.lower()
    
    # Trojan ALWAYS requires TLS
    if inbound_type == 'trojan':
        return True
    
    # Hysteria requires TLS certificate (not self-signed for production)
    if inbound_type in ['hysteria', 'hysteria2']:
        return True
    
    # Check security setting
    if security in ['tls', 'reality']:
        return True
    
    # Others don't require TLS by default
    return False


def is_node_compatible_with_inbound(
    node_address: str,
    node_domain: Optional[str],
    inbound_type: str,
    inbound_security: Optional[str] = None
) -> tuple[bool, str]:
    """
    Check if node is compatible with inbound
    
    Returns:
        (is_compatible, reason)
    """
    requires_tls = inbound_requires_tls(inbound_type, inbound_security)
    supports_tls = node_supports_tls(node_address, node_domain)
    
    if requires_tls and not supports_tls:
        return False, f"{inbound_type.upper()} with {inbound_security or 'TLS'} requires domain name, but node uses IP address"
    
    return True, "Compatible"


def get_node_server_name(node_address: str, node_domain: Optional[str] = None) -> str:
    """
    Get server name for TLS/SNI
    
    Priority:
    1. node.domain (if set)
    2. node.address (if it's a domain)
    3. Empty string (for IP-only nodes)
    """
    if node_domain and is_domain(node_domain):
        return node_domain
    
    if is_domain(node_address):
        return node_address
    
    return ""
