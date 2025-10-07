#!/usr/bin/env python3
import sqlite3
import json
import subprocess
import base64

conn = sqlite3.connect('/root/panel/backend/panel.db')
cursor = conn.cursor()

print("="*80)
print("FIXING REALITY PUBLIC KEY")
print("="*80)

# Fix Reality inbound
cursor.execute("SELECT id, tag, reality_settings FROM inbounds WHERE security = 'reality'")
reality_inbound = cursor.fetchone()

if reality_inbound:
    inbound_id, tag, reality_json = reality_inbound
    reality = json.loads(reality_json)
    private_key = reality.get('privateKey')
    
    print(f"\nReality Inbound: {tag}")
    print(f"Private Key (first 20 chars): {private_key[:20]}...")
    
    # Try to generate using xray x25519 -i key
    result = subprocess.run(
        ['/usr/local/bin/xray', 'x25519', '-i', private_key],
        capture_output=True,
        text=True
    )
    
    print(f"\nXray x25519 output:")
    print(result.stdout)
    
    # The public key should be in base64 format, 43 characters
    # Let's parse it properly
    lines = result.stdout.strip().split('\n')
    public_key = None
    
    for line in lines:
        # Look for line with Public key
        if 'Public' in line or 'public' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                # Extract just the key part
                key_part = parts[1].strip()
                # Remove any prefix like "Hash32: " if present
                if ' ' in key_part:
                    key_part = key_part.split()[-1]
                public_key = key_part
                break
    
    if public_key:
        print(f"\n✓ Extracted Public Key: {public_key}")
        
        reality['publicKey'] = public_key
        updated_json = json.dumps(reality)
        
        cursor.execute(
            "UPDATE inbounds SET reality_settings = ?, updated_at = datetime('now') WHERE id = ?",
            (updated_json, inbound_id)
        )
        print(f"✓ Updated Reality inbound with public key")
    else:
        print("✗ Could not extract public key")

print("\n" + "="*80)
print("FIXING VMESS WEBSOCKET SETTINGS")
print("="*80)

# Fix VMess stream settings
cursor.execute("SELECT id, tag, stream_settings FROM inbounds WHERE type = 'vmess' AND network = 'ws'")
vmess_inbound = cursor.fetchone()

if vmess_inbound:
    inbound_id, tag, stream_json = vmess_inbound
    
    print(f"\nVMess Inbound: {tag}")
    
    if stream_json:
        stream = json.loads(stream_json)
        print(f"Current stream settings: {json.dumps(stream, indent=2)}")
        
        # Fix: network should be 'ws', not 'tcp'
        if stream.get('network') != 'ws':
            stream['network'] = 'ws'
            
            # Ensure wsSettings exist
            if 'wsSettings' not in stream:
                stream['wsSettings'] = {
                    'path': '/vmess',
                    'headers': {}
                }
            
            updated_stream = json.dumps(stream)
            cursor.execute(
                "UPDATE inbounds SET stream_settings = ?, updated_at = datetime('now') WHERE id = ?",
                (updated_stream, inbound_id)
            )
            print(f"\n✓ Fixed VMess stream settings to use WebSocket")
        else:
            print(f"\n✓ VMess stream settings already correct")
    else:
        # Create default WS settings
        stream = {
            'network': 'ws',
            'wsSettings': {
                'path': '/vmess',
                'headers': {}
            }
        }
        updated_stream = json.dumps(stream)
        cursor.execute(
            "UPDATE inbounds SET stream_settings = ?, updated_at = datetime('now') WHERE id = ?",
            (updated_stream, inbound_id)
        )
        print(f"\n✓ Created VMess WebSocket settings")

conn.commit()
conn.close()

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("\n1. Restart API to sync configs to nodes:")
print("   systemctl restart xray-panel")
print("\n2. Wait 30 seconds for Celery to sync configs to all nodes")
print("\n3. Check node status in admin panel")
print("\n4. Generate new subscription link for testing")
