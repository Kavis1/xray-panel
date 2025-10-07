"""
External API для управления пользователями

Требует API ключ для авторизации.
Создайте API ключ через /api/v1/api-keys/
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.base import get_db
from app.models.user import User, UserProxy, UserInbound, UserStatus
from app.models.api_key import APIKey
from app.api.external_deps import verify_api_key, require_scope
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid as uuid_lib

router = APIRouter()


# Schemas для External API
class ExternalUserCreate(BaseModel):
    """Создание пользователя через External API"""
    username: str = Field(..., min_length=3, max_length=64, description="Имя пользователя (уникальное)")
    email: EmailStr = Field(..., description="Email пользователя")
    traffic_limit_gb: Optional[float] = Field(None, ge=0, description="Лимит трафика в ГБ (null = безлимит)")
    expire_days: Optional[int] = Field(None, ge=1, description="Срок действия в днях")
    description: Optional[str] = Field(None, max_length=500, description="Описание пользователя")
    
    # Настройки proxy
    protocols: Optional[List[str]] = Field(
        default=["vless"],
        description="Список протоколов для создания: vless, vmess, trojan, shadowsocks"
    )


class ExternalUserUpdate(BaseModel):
    """Обновление пользователя через External API"""
    email: Optional[EmailStr] = None
    traffic_limit_gb: Optional[float] = Field(None, ge=0)
    extend_days: Optional[int] = Field(None, ge=1, description="Продлить на N дней")
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, description="active, disabled, limited, expired")


class ExternalUserResponse(BaseModel):
    """Ответ с данными пользователя"""
    id: int
    username: str
    email: str
    status: str
    traffic_used_mb: float = Field(..., description="Использовано трафика (МБ)")
    traffic_limit_mb: Optional[float] = Field(None, description="Лимит трафика (МБ)")
    traffic_remaining_mb: Optional[float] = Field(None, description="Остаток трафика (МБ)")
    expire_at: Optional[datetime]
    created_at: datetime
    subscription_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExternalUserListResponse(BaseModel):
    total: int
    items: List[ExternalUserResponse]


class SubscriptionLinksResponse(BaseModel):
    """Ссылки на подписки"""
    universal_url: str = Field(..., description="Универсальная ссылка подписки")
    clash_url: str = Field(..., description="Clash подписка")
    singbox_url: str = Field(..., description="Sing-box подписка")
    v2ray_url: str = Field(..., description="V2ray подписка")


class UserTrafficResponse(BaseModel):
    """Статистика трафика пользователя"""
    username: str
    traffic_used_bytes: int
    traffic_used_mb: float
    traffic_used_gb: float
    traffic_limit_bytes: Optional[int]
    traffic_limit_gb: Optional[float]
    traffic_remaining_gb: Optional[float]
    usage_percent: Optional[float]


# === ENDPOINTS ===


@router.post(
    "/",
    response_model=ExternalUserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("users:write"))],
    summary="Создать пользователя",
    description="""
    Создание нового пользователя с автоматической генерацией proxy конфигураций.
    
    **Требуемый scope:** `users:write`
    
    **Автоматически создаются:**
    - UUID для VLESS/VMess протоколов
    - Пароли для Trojan/Shadowsocks
    - Привязка к доступным inbound'ам
    """
)
async def create_user(
    user_data: ExternalUserCreate,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    # Проверка существования
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{user_data.username}' already exists"
        )
    
    # Расчет лимита в байтах
    traffic_limit_bytes = None
    if user_data.traffic_limit_gb:
        traffic_limit_bytes = int(user_data.traffic_limit_gb * 1024 * 1024 * 1024)
    
    # Расчет даты истечения
    expire_at = None
    if user_data.expire_days:
        from datetime import timedelta
        expire_at = datetime.now() + timedelta(days=user_data.expire_days)
    
    # Создание пользователя
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        status=UserStatus.ACTIVE.value,
        traffic_limit_bytes=traffic_limit_bytes,
        traffic_used_bytes=0,
        traffic_limit_strategy="no_reset",
        expire_at=expire_at,
        description=user_data.description,
    )
    
    db.add(new_user)
    await db.flush()
    
    # Создание proxy конфигураций
    protocols = user_data.protocols or ["vless"]
    for protocol in protocols:
        protocol = protocol.lower()
        
        if protocol == "vless":
            proxy = UserProxy(
                user_id=new_user.id,
                type="vless",
                vless_uuid=str(uuid_lib.uuid4()),
                vless_flow="xtls-rprx-vision",
            )
        elif protocol == "vmess":
            proxy = UserProxy(
                user_id=new_user.id,
                type="vmess",
                vmess_uuid=str(uuid_lib.uuid4()),
            )
        elif protocol == "trojan":
            import secrets
            proxy = UserProxy(
                user_id=new_user.id,
                type="trojan",
                trojan_password=secrets.token_urlsafe(16),
            )
        elif protocol == "shadowsocks":
            import secrets
            proxy = UserProxy(
                user_id=new_user.id,
                type="shadowsocks",
                ss_password=secrets.token_urlsafe(16),
                ss_method="chacha20-ietf-poly1305",
            )
        else:
            continue
        
        db.add(proxy)
    
    await db.commit()
    await db.refresh(new_user)
    
    # Формирование ответа
    response = ExternalUserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        status=new_user.status,
        traffic_used_mb=new_user.traffic_used_bytes / (1024 * 1024) if new_user.traffic_used_bytes else 0,
        traffic_limit_mb=new_user.traffic_limit_bytes / (1024 * 1024) if new_user.traffic_limit_bytes else None,
        traffic_remaining_mb=(new_user.traffic_limit_bytes - new_user.traffic_used_bytes) / (1024 * 1024) if new_user.traffic_limit_bytes else None,
        expire_at=new_user.expire_at,
        created_at=new_user.created_at,
        subscription_url=f"/api/v1/external/users/{new_user.username}/subscription"
    )
    
    return response


@router.get(
    "/",
    response_model=ExternalUserListResponse,
    dependencies=[Depends(require_scope("users:read"))],
    summary="Список пользователей",
    description="""
    Получение списка пользователей с пагинацией и фильтрацией.
    
    **Требуемый scope:** `users:read`
    """
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(50, ge=1, le=200, description="Максимум записей"),
    status: Optional[str] = Query(None, description="Фильтр по статусу: active, disabled, limited, expired"),
    search: Optional[str] = Query(None, description="Поиск по username или email"),
):
    query = select(User)
    
    # Фильтры
    if status:
        query = query.where(User.status == status)
    
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    
    # Подсчет total
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()
    
    # Получение данных
    result = await db.execute(query.offset(skip).limit(limit).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    # Формирование ответов
    items = []
    for user in users:
        traffic_used_mb = user.traffic_used_bytes / (1024 * 1024) if user.traffic_used_bytes else 0
        traffic_limit_mb = user.traffic_limit_bytes / (1024 * 1024) if user.traffic_limit_bytes else None
        traffic_remaining_mb = (user.traffic_limit_bytes - user.traffic_used_bytes) / (1024 * 1024) if user.traffic_limit_bytes else None
        
        items.append(ExternalUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            status=user.status,
            traffic_used_mb=traffic_used_mb,
            traffic_limit_mb=traffic_limit_mb,
            traffic_remaining_mb=traffic_remaining_mb,
            expire_at=user.expire_at,
            created_at=user.created_at,
            subscription_url=f"/api/v1/external/users/{user.username}/subscription"
        ))
    
    return ExternalUserListResponse(total=total, items=items)


@router.get(
    "/{username}",
    response_model=ExternalUserResponse,
    dependencies=[Depends(require_scope("users:read"))],
    summary="Получить пользователя",
    description="""
    Получение детальной информации о пользователе по username.
    
    **Требуемый scope:** `users:read`
    """
)
async def get_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    traffic_used_mb = user.traffic_used_bytes / (1024 * 1024) if user.traffic_used_bytes else 0
    traffic_limit_mb = user.traffic_limit_bytes / (1024 * 1024) if user.traffic_limit_bytes else None
    traffic_remaining_mb = (user.traffic_limit_bytes - user.traffic_used_bytes) / (1024 * 1024) if user.traffic_limit_bytes else None
    
    return ExternalUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        traffic_used_mb=traffic_used_mb,
        traffic_limit_mb=traffic_limit_mb,
        traffic_remaining_mb=traffic_remaining_mb,
        expire_at=user.expire_at,
        created_at=user.created_at,
        subscription_url=f"/api/v1/external/users/{user.username}/subscription"
    )


@router.patch(
    "/{username}",
    response_model=ExternalUserResponse,
    dependencies=[Depends(require_scope("users:write"))],
    summary="Обновить пользователя",
)
async def update_user(
    username: str,
    update_data: ExternalUserUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    # Обновление полей
    if update_data.email:
        user.email = update_data.email
    
    if update_data.traffic_limit_gb is not None:
        user.traffic_limit_bytes = int(update_data.traffic_limit_gb * 1024 * 1024 * 1024)
    
    if update_data.extend_days:
        from datetime import timedelta
        if user.expire_at:
            user.expire_at += timedelta(days=update_data.extend_days)
        else:
            user.expire_at = datetime.now() + timedelta(days=update_data.extend_days)
    
    if update_data.description is not None:
        user.description = update_data.description
    
    if update_data.status:
        user.status = update_data.status
    
    await db.commit()
    await db.refresh(user)
    
    traffic_used_mb = user.traffic_used_bytes / (1024 * 1024) if user.traffic_used_bytes else 0
    traffic_limit_mb = user.traffic_limit_bytes / (1024 * 1024) if user.traffic_limit_bytes else None
    traffic_remaining_mb = (user.traffic_limit_bytes - user.traffic_used_bytes) / (1024 * 1024) if user.traffic_limit_bytes else None
    
    return ExternalUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        traffic_used_mb=traffic_used_mb,
        traffic_limit_mb=traffic_limit_mb,
        traffic_remaining_mb=traffic_remaining_mb,
        expire_at=user.expire_at,
        created_at=user.created_at,
        subscription_url=f"/api/v1/external/users/{user.username}/subscription"
    )


@router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("users:delete"))],
    summary="Удалить пользователя",
)
async def delete_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    await db.delete(user)
    await db.commit()


@router.get(
    "/{username}/subscription",
    response_model=SubscriptionLinksResponse,
    dependencies=[Depends(require_scope("subscriptions:read"))],
    summary="Получить ссылки подписки",
)
async def get_subscription_links(
    username: str,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    from app.core.config import settings
    base_url = settings.XRAY_SUBSCRIPTION_URL_PREFIX
    
    return SubscriptionLinksResponse(
        universal_url=f"{base_url}/{username}",
        clash_url=f"{base_url}/{username}?format=clash",
        singbox_url=f"{base_url}/{username}/singbox",
        v2ray_url=f"{base_url}/{username}?format=v2ray"
    )


@router.get(
    "/{username}/traffic",
    response_model=UserTrafficResponse,
    dependencies=[Depends(require_scope("stats:read"))],
    summary="Статистика трафика пользователя",
)
async def get_user_traffic(
    username: str,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    traffic_used_mb = user.traffic_used_bytes / (1024 * 1024) if user.traffic_used_bytes else 0
    traffic_used_gb = traffic_used_mb / 1024
    traffic_limit_gb = user.traffic_limit_bytes / (1024 * 1024 * 1024) if user.traffic_limit_bytes else None
    traffic_remaining_gb = (user.traffic_limit_bytes - user.traffic_used_bytes) / (1024 * 1024 * 1024) if user.traffic_limit_bytes else None
    usage_percent = (user.traffic_used_bytes / user.traffic_limit_bytes * 100) if user.traffic_limit_bytes else None
    
    return UserTrafficResponse(
        username=user.username,
        traffic_used_bytes=user.traffic_used_bytes,
        traffic_used_mb=traffic_used_mb,
        traffic_used_gb=traffic_used_gb,
        traffic_limit_bytes=user.traffic_limit_bytes,
        traffic_limit_gb=traffic_limit_gb,
        traffic_remaining_gb=traffic_remaining_gb,
        usage_percent=usage_percent
    )


@router.post(
    "/{username}/reset-traffic",
    dependencies=[Depends(require_scope("users:write"))],
    summary="Сбросить трафик пользователя",
)
async def reset_user_traffic(
    username: str,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    user.traffic_used_bytes = 0
    await db.commit()
    
    return {"message": f"Traffic reset for user '{username}'"}
