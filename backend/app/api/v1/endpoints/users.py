from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.base import get_db
from app.models.admin import Admin
from app.models.user import User, UserProxy, UserInbound, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse, UserListItem
from app.api.deps import get_current_admin
import uuid as uuid_lib

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
):
    query = select(User)
    
    if status:
        query = query.where(User.status == status.value)
    
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()
    
    result = await db.execute(query.offset(skip).limit(limit))
    users = result.scalars().all()
    
    return UserListResponse(total=total, items=users)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # Generate unique subscription token
    while True:
        subscription_token = generate_subscription_token()
        token_check = await db.execute(select(User).where(User.subscription_token == subscription_token))
        if token_check.scalar_one_or_none() is None:
            break
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        subscription_token=subscription_token,
        status=user_data.status.value,
        traffic_limit_bytes=user_data.traffic_limit_bytes,
        traffic_limit_strategy=user_data.traffic_limit_strategy.value,
        expire_at=user_data.expire_at,
        description=user_data.description,
        telegram_id=user_data.telegram_id,
        hwid_device_limit=user_data.hwid_device_limit,
    )
    
    db.add(new_user)
    await db.flush()
    
    # Normalize proxy types to lowercase
    if user_data.proxies:
        for proxy_data in user_data.proxies:
            if proxy_data.type:
                proxy_data.type = ProxyType(proxy_data.type.value.lower())
    
    # Автоматически создаем proxy если не указаны
    if not user_data.proxies or len(user_data.proxies) == 0:
        # Создаем VLESS proxy по умолчанию
        default_proxy = UserProxy(
            user_id=new_user.id,
            type="VLESS",
            vless_uuid=str(uuid_lib.uuid4()),
            vless_flow="xtls-rprx-vision",
        )
        db.add(default_proxy)
    else:
        for proxy_data in user_data.proxies:
            proxy = UserProxy(
                user_id=new_user.id,
                type=proxy_data.type.value,
                vmess_uuid=proxy_data.vmess_uuid or (str(uuid_lib.uuid4()) if proxy_data.type.value in ["VMESS", "VLESS"] else None),
                vless_uuid=proxy_data.vless_uuid,
                vless_flow=proxy_data.vless_flow,
                trojan_password=proxy_data.trojan_password,
                ss_password=proxy_data.ss_password,
                ss_method=proxy_data.ss_method,
                network=proxy_data.network,
                security=proxy_data.security,
                sni=proxy_data.sni,
                alpn=proxy_data.alpn,
                fingerprint=proxy_data.fingerprint,
            )
            db.add(proxy)
    
    if user_data.inbound_tags:
        for tag in user_data.inbound_tags:
            inbound = UserInbound(user_id=new_user.id, inbound_tag=tag)
            db.add(inbound)
    
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "status": new_user.status,
        "traffic_limit_bytes": new_user.traffic_limit_bytes,
        "traffic_used_bytes": new_user.traffic_used_bytes,
        "traffic_limit_strategy": new_user.traffic_limit_strategy,
        "expire_at": new_user.expire_at,
        "sub_revoked_at": new_user.sub_revoked_at,
        "online_at": new_user.online_at,
        "description": new_user.description,
        "telegram_id": new_user.telegram_id,
        "hwid_device_limit": new_user.hwid_device_limit,
        "created_at": new_user.created_at,
        "updated_at": new_user.updated_at,
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Remove password if empty or less than 6 characters
    if "password" in update_data:
        if not update_data["password"] or len(update_data["password"]) < 6:
            del update_data["password"]
        # If updating password, hash it (add hashing logic if needed)
    
    if "status" in update_data:
        update_data["status"] = update_data["status"].value
    if "traffic_limit_strategy" in update_data:
        update_data["traffic_limit_strategy"] = update_data["traffic_limit_strategy"].value
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "status": user.status,
        "traffic_limit_bytes": user.traffic_limit_bytes,
        "traffic_used_bytes": user.traffic_used_bytes,
        "traffic_limit_strategy": user.traffic_limit_strategy,
        "expire_at": user.expire_at,
        "sub_revoked_at": user.sub_revoked_at,
        "online_at": user.online_at,
        "description": user.description,
        "telegram_id": user.telegram_id,
        "hwid_device_limit": user.hwid_device_limit,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    await db.delete(user)
    await db.commit()


@router.post("/{user_id}/reset-traffic")
async def reset_user_traffic(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.traffic_used_bytes = 0
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "status": user.status,
        "traffic_limit_bytes": user.traffic_limit_bytes,
        "traffic_used_bytes": user.traffic_used_bytes,
        "traffic_limit_strategy": user.traffic_limit_strategy,
        "expire_at": user.expire_at,
        "sub_revoked_at": user.sub_revoked_at,
        "online_at": user.online_at,
        "description": user.description,
        "telegram_id": user.telegram_id,
        "hwid_device_limit": user.hwid_device_limit,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "message": "Traffic reset successfully"
    }


@router.post("/{user_id}/revoke-sub")
async def revoke_user_subscription(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    from datetime import datetime
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.sub_revoked_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Subscription revoked successfully"}
