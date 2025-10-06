#!/usr/bin/env python3
"""
Generate sing-box configuration for Hysteria protocols
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.inbound import Inbound
from app.services.singbox.config_builder import SingBoxConfigBuilder
from app.db.base import async_session_maker


async def generate_singbox_config():
    """Generate sing-box configuration from database"""
    
    async with async_session_maker() as db:
        # Get enabled Hysteria inbounds
        result = await db.execute(
            select(Inbound).where(
                Inbound.is_enabled == True,
                Inbound.type.in_(["HYSTERIA", "HYSTERIA2"])
            )
        )
        inbounds = result.scalars().all()
        
        if not inbounds:
            print("No Hysteria inbounds found, generating empty config")
            return {
                "log": {"level": "warn"},
                "inbounds": [],
                "outbounds": [{"type": "direct", "tag": "direct"}]
            }
        
        # Get active users with proxies
        result = await db.execute(
            select(User)
            .options(selectinload(User.proxies))
            .options(selectinload(User.inbounds))
            .where(User.status == "ACTIVE")
        )
        users = result.scalars().all()
        
        # Build sing-box configuration
        builder = SingBoxConfigBuilder()
        
        for inbound in inbounds:
            # Get users assigned to this inbound
            inbound_users = []
            for user in users:
                if any(ui.inbound_tag == inbound.tag for ui in user.inbounds):
                    # Convert user to dict with proxies
                    user_proxies = []
                    for proxy in user.proxies:
                        password = ""
                        if proxy.type == "HYSTERIA":
                            password = proxy.hysteria_password or ""
                        elif proxy.type == "HYSTERIA2":
                            password = proxy.hysteria2_password or ""
                        elif proxy.type == "TROJAN":
                            password = proxy.trojan_password or ""
                        elif proxy.type == "SHADOWSOCKS":
                            password = proxy.ss_password or ""
                        
                        user_proxies.append({
                            "type": proxy.type,
                            "password": password
                        })
                    
                    inbound_users.append({
                        "email": user.email,
                        "proxies": user_proxies
                    })
            
            if not inbound_users:
                continue
            
            if inbound.type == "HYSTERIA":
                builder.add_hysteria_inbound(inbound, inbound_users)
            elif inbound.type == "HYSTERIA2":
                builder.add_hysteria2_inbound(inbound, inbound_users)
        
        config_json = builder.build()
        return json.loads(config_json)


async def main():
    """Main entry point"""
    try:
        config = await generate_singbox_config()
        
        # Write to file
        output_path = Path("/tmp/singbox_config.json")
        output_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
        
        print(f"✅ Sing-box config generated: {output_path}")
        print(f"   Inbounds: {len(config.get('inbounds', []))}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating sing-box config: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
