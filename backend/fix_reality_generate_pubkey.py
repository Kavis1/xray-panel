#!/usr/bin/env python3
import sqlite3
import json
import base64

try:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: cryptography library not installed")
    print("Installing...")
    import subprocess
    subprocess.run(['pip', 'install', 'cryptography'], check=True)
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization

conn = sqlite3.connect('/root/panel/backend/panel.db')
cursor = conn.cursor()

print("="*80)
print("GENERATING REALITY PUBLIC KEY FROM PRIVATE KEY")
print("="*80)

# Get Reality inbound
cursor.execute("SELECT id, tag, reality_settings FROM inbounds WHERE security = 'reality'")
reality_inbound = cursor.fetchone()

if not reality_inbound:
    print("ERROR: No Reality inbound found")
    exit(1)

inbound_id, tag, reality_json = reality_inbound
reality = json.loads(reality_json)

private_key_b64 = reality.get('privateKey')
if not private_key_b64:
    print("ERROR: No private key found in Reality settings")
    exit(1)

print(f"\nReality Inbound: {tag}")
print(f"Private Key (base64): {private_key_b64[:20]}...")

try:
    # Decode base64 private key
    private_key_bytes = base64.b64decode(private_key_b64)
    
    # Create X25519PrivateKey object
    private_key = X25519PrivateKey.from_private_bytes(private_key_bytes)
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize public key to bytes
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    # Encode to base64
    public_key_b64 = base64.b64encode(public_key_bytes).decode('utf-8')
    
    print(f"\n✓ Generated Public Key: {public_key_b64}")
    
    # Update reality settings
    reality['publicKey'] = public_key_b64
    updated_json = json.dumps(reality)
    
    cursor.execute(
        "UPDATE inbounds SET reality_settings = ?, updated_at = datetime('now') WHERE id = ?",
        (updated_json, inbound_id)
    )
    conn.commit()
    
    print(f"\n✓ Updated Reality inbound '{tag}' with public key")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Restart xray-panel service to sync config to nodes:")
    print("   systemctl restart xray-panel")
    print("\n2. Wait 30 seconds for Celery to push configs")
    print("\n3. Check /root/panel/backend/show_subscription_links.py to get updated links")
    print("\n4. Test connection in VPN client")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n⚠️  Alternative: Generate NEW keypair")
    print("\nWould you like to generate a completely new keypair? (yes/no)")
    print("WARNING: This will invalidate existing client configs!")

conn.close()
