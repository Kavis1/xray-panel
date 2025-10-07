#!/usr/bin/env python3
import sqlite3
import json
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

conn = sqlite3.connect('/root/panel/backend/panel.db')
cursor = conn.cursor()

print("="*80)
print("GENERATING NEW REALITY KEYPAIR")
print("="*80)

# Get Reality inbound
cursor.execute("SELECT id, tag, reality_settings FROM inbounds WHERE security = 'reality'")
reality_inbound = cursor.fetchone()

if not reality_inbound:
    print("ERROR: No Reality inbound found")
    exit(1)

inbound_id, tag, reality_json = reality_inbound
reality = json.loads(reality_json)

print(f"\nReality Inbound: {tag}")
print(f"\n⚠️  WARNING: This will generate NEW keys")
print("   Current client configs will STOP working until updated!")

# Generate new X25519 keypair
print("\nGenerating new X25519 keypair...")
private_key = X25519PrivateKey.generate()

# Get private key bytes
private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
)

# Get public key
public_key = private_key.public_key()
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)

# Encode to base64
private_key_b64 = base64.b64encode(private_key_bytes).decode('utf-8')
public_key_b64 = base64.b64encode(public_key_bytes).decode('utf-8')

print(f"\n✓ New Private Key: {private_key_b64}")
print(f"✓ New Public Key: {public_key_b64}")

# Update reality settings
reality['privateKey'] = private_key_b64
reality['publicKey'] = public_key_b64

updated_json = json.dumps(reality, indent=2)

print(f"\n✓ Updated Reality settings:")
print(updated_json)

cursor.execute(
    "UPDATE inbounds SET reality_settings = ?, updated_at = datetime('now') WHERE id = ?",
    (json.dumps(reality), inbound_id)
)
conn.commit()

print(f"\n✓ Saved to database")

print("\n" + "="*80)
print("NEXT STEPS - VERY IMPORTANT!")
print("="*80)
print("\n1. Restart xray-panel service:")
print("   systemctl restart xray-panel")
print("\n2. Wait 30-60 seconds for Celery to sync to all nodes")
print("\n3. Generate new subscription links:")
print("   python3 /root/panel/backend/show_subscription_links.py")
print("\n4. Send NEW links to all users (old ones won't work)")
print("\n5. Test Reality connection in VPN client")

print(f"\n✓ Reality inbound '{tag}' updated with new keypair")

conn.close()
