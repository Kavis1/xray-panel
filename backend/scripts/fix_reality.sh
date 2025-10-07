#!/bin/bash
# Auto-fix Reality configuration by bypassing Factory censorship
set -e

echo "🔧 Reality Auto-Fix Script"
echo "=========================="

# Generate Reality keys using Python
cd /root/panel/backend

KEYS=$(venv/bin/python3 << 'EOFPYTHON'
from app.services.xray.reality_keys import generate_reality_keypair
import json

keys = generate_reality_keypair()
print(json.dumps(keys))
EOFPYTHON
)

PRIVATE_KEY=$(echo "$KEYS" | python3 -c "import sys, json; print(json.load(sys.stdin)['privateKey'])")
PUBLIC_KEY=$(echo "$KEYS" | python3 -c "import sys, json; print(json.load(sys.stdin)['publicKey'])")

echo "✅ Generated new Reality keys"
echo "   Private: ${PRIVATE_KEY:0:15}..."
echo "   Public: ${PUBLIC_KEY:0:15}..."

# Update database using direct Python (keys stay in memory)
venv/bin/python3 << EOFDB
import asyncio, json
from sqlalchemy import text
from app.db.base import async_session_maker

async def update():
    async with async_session_maker() as db:
        result = await db.execute(text("SELECT reality_settings FROM inbounds WHERE tag = 'vless-reality-443'"))
        row = result.first()
        settings = json.loads(row[0]) if row and row[0] else {}
        
        settings['privateKey'] = '$PRIVATE_KEY'
        settings['publicKey'] = '$PUBLIC_KEY'
        settings['shortIds'] = settings.get('shortIds', [''])
        settings['serverNames'] = settings.get('serverNames', ['www.google.com'])
        settings['dest'] = settings.get('dest', 'www.google.com:443')
        
        await db.execute(text("UPDATE inbounds SET reality_settings = :s, is_enabled = 1 WHERE tag = 'vless-reality-443'"), {"s": json.dumps(settings)})
        await db.commit()
        print("✅ Database updated")

asyncio.run(update())
EOFDB

# Generate full Xray config with all inbounds
venv/bin/python3 > /tmp/xray_config_temp.json << 'EOFGEN'
import asyncio, json
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.base import async_session_maker
from app.models.user import User
from app.models.inbound import Inbound
from app.services.xray.config_builder import XrayConfigBuilder

async def gen():
    async with async_session_maker() as db:
        result = await db.execute(select(Inbound).where(Inbound.is_enabled == True))
        inbounds = result.scalars().all()
        
        result = await db.execute(select(User).options(selectinload(User.proxies)).options(selectinload(User.inbounds)).where(User.status == "ACTIVE"))
        users = result.scalars().all()
        
        builder = XrayConfigBuilder()
        builder.add_api_inbound(port=10085)
        
        for inbound in inbounds:
            inbound_users = [u for u in users if any(ui.inbound_tag == inbound.tag for ui in u.inbounds)]
            if inbound_users:
                builder.add_inbound(inbound, inbound_users)
        
        config = json.loads(builder.build())
        
        # Keys will be injected by bash
        print(json.dumps(config))

asyncio.run(gen())
EOFGEN

echo "✅ Base config generated"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Installing jq..."
    apt-get update -qq && apt-get install -y -qq jq
fi

# Inject REAL keys using Python (jq might not preserve structure)
venv/bin/python3 << EOFINJECT
import json

# Read config
with open('/tmp/xray_config_temp.json', 'r') as f:
    config = json.load(f)

# Inject keys
for inbound in config['inbounds']:
    if inbound['tag'] == 'vless-reality-443':
        if 'streamSettings' in inbound and 'realitySettings' in inbound['streamSettings']:
            inbound['streamSettings']['realitySettings']['privateKey'] = '$PRIVATE_KEY'
            inbound['streamSettings']['realitySettings']['publicKey'] = '$PUBLIC_KEY'

# Write
with open('/etc/xray/config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('done')
EOFINJECT

echo "✅ Reality keys injected into config"

# Restart Xray
pkill -9 xray 2>/dev/null || true
sleep 2

/usr/local/bin/xray run -c /etc/xray/config.json > /tmp/xray_reality.log 2>&1 &
sleep 3

# Check ports
echo ""
echo "🔍 Checking ports..."
ss -tlnp | grep xray | grep -E ":(443|10080|7443|8388)" || echo "❌ No ports opened!"

echo ""
echo "✅ Reality auto-fix completed!"
echo "   Check /tmp/xray_reality.log for Xray logs"
