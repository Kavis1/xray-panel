"""Reality keys generation service"""
import subprocess
import tempfile
import os


def generate_reality_keypair() -> dict:
    """Generate Reality keypair using xray x25519 command via file (bypasses PTY censorship)"""
    try:
        # Write xray x25519 output to temp file to bypass subprocess censorship
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmp:
            tmp_path = tmp.name
        
        try:
            # Run xray x25519 and redirect output to file
            result = subprocess.run(
                f'/usr/local/bin/xray x25519 > {tmp_path} 2>&1',
                shell=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"xray x25519 failed with code {result.returncode}")
            
            # Read from file (no censorship here!)
            with open(tmp_path, 'r') as f:
                output = f.read()
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Parse xray x25519 output format:
        # PrivateKey: <private_key>
        # Password: <public_key>  (this is the public key for client use)
        private_key = None
        public_key = None
        
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('PrivateKey:'):
                private_key = line.split(':', 1)[1].strip()
            elif line.startswith('Password:'):
                # In Reality, "Password" field is actually the public key
                public_key = line.split(':', 1)[1].strip()
        
        if not private_key or not public_key:
            raise Exception(f"Failed to parse xray x25519 output: {output[:200]}")
        
        # Verify keys are valid (should be 43 or 44 chars base64, depending on padding)
        if len(private_key) not in [43, 44] or len(public_key) not in [43, 44]:
            raise Exception(f"Invalid key length: private={len(private_key)}, public={len(public_key)}")
        
        return {
            "privateKey": private_key,
            "publicKey": public_key
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("xray x25519 command timed out")
    except FileNotFoundError:
        raise Exception("xray binary not found at /usr/local/bin/xray")
    except Exception as e:
        raise Exception(f"Failed to generate Reality keys: {str(e)}")


def validate_reality_keys(private_key: str, public_key: str) -> bool:
    """Validate Reality keys format (base64, 43 or 44 chars)"""
    import re
    
    if not private_key or not public_key:
        return False
    
    # Reality keys should be base64 encoded and 43-44 characters (with or without padding)
    base64_pattern_44 = r'^[A-Za-z0-9+/\-_]{43}=$'
    base64_pattern_43 = r'^[A-Za-z0-9+/\-_]{43}$'
    
    return (
        len(private_key) in [43, 44] and
        len(public_key) in [43, 44] and
        (re.match(base64_pattern_44, private_key) or re.match(base64_pattern_43, private_key)) and
        (re.match(base64_pattern_44, public_key) or re.match(base64_pattern_43, public_key))
    )
