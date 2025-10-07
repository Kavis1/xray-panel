#!/usr/bin/env python3
import sqlite3
import json
import subprocess

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

# Generate new keypair
print("\nGenerating new x25519 keypair...")
result = subprocess.run(
    ['/usr/local/bin/xray', 'x25519'],
    capture_output=True,
    text=True
)

print("\nXray x25519 output:")
print(result.stdout)

# Parse output - format should be:
# Private key: xxx
# Public key: yyy
lines = result.stdout.strip().split('\n')

private_key = None
public_key = None

for line in lines:
    line_lower = line.lower()
    if 'private' in line_lower and 'key' in line_lower:
        parts = line.split(':', 1)
        if len(parts) == 2:
            private_key = parts[1].strip()
    elif 'public' in line_lower and 'key' in line_lower:
        parts = line.split(':', 1)
        if len(parts) == 2:
            public_key = parts[1].strip()

if private_key and public_key:
    print(f"\n✓ Generated Private Key: {private_key[:20]}...")
    print(f"✓ Generated Public Key: {public_key}")
    
    # Update reality settings with new keys
    reality['privateKey'] = private_key
    reality['publicKey'] = public_key
    
    updated_json = json.dumps(reality)
    
    cursor.execute(
        "UPDATE inbounds SET reality_settings = ?, updated_at = datetime('now') WHERE id = ?",
        (updated_json, inbound_id)
    )
    conn.commit()
    
    print(f"\n✓ Updated Reality inbound with new keypair")
    print("\n" + "="*80)
    print("IMPORTANT: You MUST restart the panel to sync to nodes!")
    print("="*80)
    print("\nRun: systemctl restart xray-panel")
    print("\nThen wait 30 seconds for Celery to push config to all nodes.")
else:
    print("\n✗ ERROR: Could not parse keypair from xray output")
    print("Trying alternative approach...")
    
    # Maybe the output format is different - try to use existing private key
    # and just assume the "Password" line is actually the public key?
    for line in lines:
        if 'Password:' in line:
            # Password in Reality context might be the shared secret (public key)
            potential_key = line.split(':', 1)[1].strip()
            print(f"\nFound Password field: {potential_key[:20]}...")
            
            response = input("\nUse this as public key? (yes/no): ")
            if response.lower() == 'yes':
                reality['publicKey'] = potential_key
                updated_json = json.dumps(reality)
                cursor.execute(
                    "UPDATE inbounds SET reality_settings = ?, updated_at = datetime('now') WHERE id = ?",
                    (updated_json, inbound_id)
                )
                conn.commit()
                print("✓ Updated")

conn.close()
