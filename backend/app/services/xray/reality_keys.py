"""Reality keys generation service"""
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def generate_reality_keypair() -> dict:
    """Generate Reality keypair using Python cryptography library"""
    try:
        # Generate X25519 keypair
        private_key_obj = X25519PrivateKey.generate()
        public_key_obj = private_key_obj.public_key()
        
        # Get raw bytes
        private_bytes = private_key_obj.private_bytes_raw()
        public_bytes = public_key_obj.public_bytes_raw()
        
        # Encode to base64 (Reality format)
        private_key = base64.b64encode(private_bytes).decode('utf-8')
        public_key = base64.b64encode(public_bytes).decode('utf-8')
        
        return {
            "privateKey": private_key,
            "publicKey": public_key
        }
        
    except Exception as e:
        raise Exception(f"Failed to generate Reality keys: {str(e)}")


def validate_reality_keys(private_key: str, public_key: str) -> bool:
    """Validate Reality keys format (base64, 44 chars)"""
    import re
    
    if not private_key or not public_key:
        return False
    
    # Reality keys should be base64 encoded and 44 characters
    base64_pattern = r'^[A-Za-z0-9+/]{43}=$'
    
    return (
        len(private_key) == 44 and
        len(public_key) == 44 and
        re.match(base64_pattern, private_key) and
        re.match(base64_pattern, public_key)
    )
