#!/usr/bin/env python3
"""
Скрипт для создания proxy для существующих пользователей без них
"""
import asyncio
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.user import User, UserProxy


async def create_missing_proxies():
    """Создать proxy для пользователей без них"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users")
        
        for user in users:
            # Check if user has proxies
            proxy_result = await session.execute(
                select(UserProxy).where(UserProxy.user_id == user.id)
            )
            proxies = proxy_result.scalars().all()
            
            if not proxies:
                print(f"Creating proxy for user {user.username} (id={user.id})")
                
                # Create default VLESS proxy
                new_proxy = UserProxy(
                    user_id=user.id,
                    type="VLESS",
                    vless_uuid=str(uuid.uuid4()),
                    vless_flow="xtls-rprx-vision",
                )
                session.add(new_proxy)
                print(f"  - Created VLESS proxy with UUID: {new_proxy.vless_uuid}")
            else:
                print(f"User {user.username} already has {len(proxies)} proxy(ies)")
        
        await session.commit()
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(create_missing_proxies())
