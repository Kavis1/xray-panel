# Additional endpoints for user management

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.base import get_db
from app.models.admin import Admin
from app.models.user import User, UserProxy, UserInbound
from app.models.inbound import Inbound
from app.api.deps import get_current_admin

router = APIRouter()


class UserProxiesResponse(BaseModel):
    user_id: int
    username: str
    proxies: List[dict]
    subscription_link: str


class AssignInboundRequest(BaseModel):
    inbound_ids: List[int]


@router.get("/{user_id}/proxies")
async def get_user_proxies(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Получить все proxies (ключи) пользователя"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get user proxies
    proxy_result = await db.execute(
        select(UserProxy).where(UserProxy.user_id == user_id)
    )
    proxies = proxy_result.scalars().all()
    
    proxies_list = []
    for proxy in proxies:
        proxy_dict = {
            "id": proxy.id,
            "type": proxy.type,
        }
        
        if proxy.type == "VLESS":
            proxy_dict["uuid"] = proxy.vless_uuid
            proxy_dict["flow"] = proxy.vless_flow
        elif proxy.type == "VMESS":
            proxy_dict["uuid"] = proxy.vmess_uuid
        elif proxy.type == "TROJAN":
            proxy_dict["password"] = proxy.trojan_password
        elif proxy.type == "SHADOWSOCKS":
            proxy_dict["password"] = proxy.ss_password
            proxy_dict["method"] = proxy.ss_method
        
        proxies_list.append(proxy_dict)
    
    # Generate subscription link
    from app.core.config import settings
    subscription_link = f"{settings.XRAY_SUBSCRIPTION_URL_PREFIX}/{user.username}"
    
    return {
        "user_id": user.id,
        "username": user.username,
        "proxies": proxies_list,
        "subscription_link": subscription_link,
        "message": "Use subscription link in your client"
    }


@router.post("/{user_id}/assign-inbounds")
async def assign_inbounds_to_user(
    user_id: int,
    request: AssignInboundRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Присвоить inbound'ы пользователю"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Remove existing inbound assignments
    await db.execute(
        select(UserInbound).where(UserInbound.user_id == user_id)
    )
    existing = (await db.execute(
        select(UserInbound).where(UserInbound.user_id == user_id)
    )).scalars().all()
    
    for item in existing:
        await db.delete(item)
    
    # Add new inbound assignments
    for inbound_id in request.inbound_ids:
        # Verify inbound exists
        inbound_result = await db.execute(
            select(Inbound).where(Inbound.id == inbound_id)
        )
        inbound = inbound_result.scalar_one_or_none()
        
        if inbound:
            user_inbound = UserInbound(
                user_id=user_id,
                inbound_tag=inbound.tag
            )
            db.add(user_inbound)
    
    await db.commit()
    
    return {
        "user_id": user_id,
        "username": user.username,
        "assigned_inbounds": request.inbound_ids,
        "message": f"Assigned {len(request.inbound_ids)} inbound(s) to user"
    }


@router.get("/{user_id}/inbounds")
async def get_user_inbounds(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Получить inbound'ы присвоенные пользователю"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get user inbounds
    user_inbounds_result = await db.execute(
        select(UserInbound).where(UserInbound.user_id == user_id)
    )
    user_inbounds = user_inbounds_result.scalars().all()
    
    inbound_tags = [ui.inbound_tag for ui in user_inbounds]
    
    # Get full inbound data
    if inbound_tags:
        inbounds_result = await db.execute(
            select(Inbound).where(Inbound.tag.in_(inbound_tags))
        )
        inbounds = inbounds_result.scalars().all()
        
        inbounds_list = [
            {
                "id": ib.id,
                "tag": ib.tag,
                "type": ib.type,
                "port": ib.port,
                "remark": ib.remark
            }
            for ib in inbounds
        ]
    else:
        inbounds_list = []
    
    return {
        "user_id": user_id,
        "username": user.username,
        "inbounds": inbounds_list,
        "count": len(inbounds_list)
    }
