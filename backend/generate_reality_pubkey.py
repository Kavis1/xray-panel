#!/usr/bin/env python3
import sqlite3
import json
import subprocess

conn = sqlite3.connect('/root/panel/backend/panel.db')
cursor = conn.cursor()

# Get Reality inbound
cursor.execute("SELECT id, tag, reality_settings FROM inbounds WHERE security = 'reality'")
inbound = cursor.fetchone()

if not inbound:
    print("No Reality inbound found")
    exit(1)

inbound_id, tag, reality_json = inbound
reality = json.loads(reality_json)

private_key = reality.get('privateKey')
if not private_key:
    print("ERROR: No private key found in Reality settings")
    exit(1)

print(f"Reality Inbound: {tag}")
print(f"Private Key: {private_key[:30]}...")

# Check if xray is available
try:
    result = subprocess.run(['which', 'xray'], capture_output=True, text=True)
    if result.returncode != 0:
        print("\nERROR: xray binary not found")
        print("Checking /usr/local/bin/xray...")
        xray_path = '/usr/local/bin/xray'
    else:
        xray_path = result.stdout.strip()
    
    print(f"\nUsing xray: {xray_path}")
    
    # Generate public key using xray x25519
    print("\nGenerating public key from private key...")
    result = subprocess.run(
        [xray_path, 'x25519', '-i', private_key],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"ERROR: Failed to generate public key")
        print(f"STDERR: {result.stderr}")
        exit(1)
    
    # Parse output - format is usually:
    # Private key: xxx
    # Public key: yyy
    output_lines = result.stdout.strip().split('\n')
    public_key = None
    
    for line in output_lines:
        if 'Public key:' in line or 'public key:' in line:
            public_key = line.split(':', 1)[1].strip()
            break
    
    if not public_key:
        # Try alternative parsing - maybe just the key is returned
        if len(output_lines) > 0:
            public_key = output_lines[-1].strip()
    
    if not public_key:
        print("ERROR: Could not parse public key from output:")
        print(result.stdout)
        exit(1)
    
    print(f"\n✓ Generated Public Key: {public_key}")
    
    # Update reality settings
    reality['publicKey'] = public_key
    updated_json = json.dumps(reality)
    
    cursor.execute(
        "UPDATE inbounds SET reality_settings = ?, updated_at = datetime('now') WHERE id = ?",
        (updated_json, inbound_id)
    )
    conn.commit()
    
    print(f"\n✓ Updated inbound '{tag}' with public key")
    print("\n⚠️  IMPORTANT: You need to sync this config to all nodes!")
    print("   Run: systemctl restart xray-panel  # to sync configs")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

conn.close()
