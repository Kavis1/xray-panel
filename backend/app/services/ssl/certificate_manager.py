"""SSL Certificate management for node authentication"""
import os
import logging
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class CertificateManager:
    """Manage SSL certificates for node authentication"""
    
    CERT_DIR = Path("/opt/xray-panel/ssl")
    CA_KEY_FILE = CERT_DIR / "ca-key.pem"
    CA_CERT_FILE = CERT_DIR / "ca-cert.pem"
    
    def __init__(self):
        self.CERT_DIR.mkdir(parents=True, exist_ok=True)
        
    def ensure_ca_exists(self) -> None:
        """Create CA certificate if it doesn't exist"""
        if self.CA_KEY_FILE.exists() and self.CA_CERT_FILE.exists():
            logger.info("CA certificate already exists")
            return
        
        logger.info("Generating new CA certificate...")
        
        # Generate CA private key
        ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Generate CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Xray Panel"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Xray Panel CA"),
        ])
        
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=0),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256(), backend=default_backend())
        )
        
        # Save CA private key
        with open(self.CA_KEY_FILE, "wb") as f:
            f.write(
                ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        
        # Save CA certificate
        with open(self.CA_CERT_FILE, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        
        logger.info(f"CA certificate created: {self.CA_CERT_FILE}")
        
    def generate_node_certificate(self, node_id: int, node_name: str, node_address: str) -> Dict[str, str]:
        """
        Generate SSL client certificate for a node
        
        Args:
            node_id: Node ID
            node_name: Node name
            node_address: Node IP address
            
        Returns:
            Dict with certificate, private key, and CA certificate
        """
        self.ensure_ca_exists()
        
        # Load CA key and certificate
        with open(self.CA_KEY_FILE, "rb") as f:
            ca_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        with open(self.CA_CERT_FILE, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())
        
        # Generate node private key
        node_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Xray Panel"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"node-{node_id}"),
        ])
        
        # Generate node certificate
        node_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(node_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))  # 1 year
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                    ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=True,
            )
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(node_name),
                    x509.IPAddress(node_address) if ":" not in node_address else x509.DNSName(node_address),
                ]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256(), backend=default_backend())
        )
        
        # Convert to PEM format
        node_cert_pem = node_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        node_key_pem = node_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode('utf-8')
        ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        
        # Save to files
        node_dir = self.CERT_DIR / f"node-{node_id}"
        node_dir.mkdir(exist_ok=True)
        
        cert_file = node_dir / "cert.pem"
        key_file = node_dir / "key.pem"
        
        with open(cert_file, "w") as f:
            f.write(node_cert_pem)
        
        with open(key_file, "w") as f:
            f.write(node_key_pem)
        
        logger.info(f"Generated certificate for node {node_id} ({node_name})")
        
        return {
            "certificate": node_cert_pem,
            "private_key": node_key_pem,
            "ca_certificate": ca_cert_pem,
            "cert_file": str(cert_file),
            "key_file": str(key_file),
        }
    
    def get_ca_certificate(self) -> str:
        """Get CA certificate for nodes to verify panel"""
        self.ensure_ca_exists()
        
        with open(self.CA_CERT_FILE, "r") as f:
            return f.read()
    
    def revoke_node_certificate(self, node_id: int) -> None:
        """Revoke node certificate (delete files)"""
        node_dir = self.CERT_DIR / f"node-{node_id}"
        
        if node_dir.exists():
            import shutil
            shutil.rmtree(node_dir)
            logger.info(f"Revoked certificate for node {node_id}")
