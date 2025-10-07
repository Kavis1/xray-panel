from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db.base import get_db
from app.models.api_key import APIKey
from app.core.api_key_manager import hash_api_key, validate_api_key_format, check_scope_permission
from app.core.rate_limiter import rate_limiter

security = HTTPBearer()


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """
    Проверка API ключа
    
    Проверяет:
    - Формат ключа
    - Существование в БД
    - Статус (active, not revoked)
    - Срок действия
    - IP whitelist
    - Rate limiting
    """
    api_key_str = credentials.credentials
    
    # Проверка формата
    if not validate_api_key_format(api_key_str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    # Хэширование и поиск в БД
    key_hash = hash_api_key(api_key_str)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Проверка статуса
    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is inactive"
        )
    
    if api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has been revoked"
        )
    
    # Проверка срока действия
    if api_key.expire_at and api_key.expire_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has expired"
        )
    
    # Проверка IP whitelist
    if api_key.allowed_ips:
        client_ip = request.client.host
        if client_ip not in api_key.allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied from IP: {client_ip}"
            )
    
    # Rate limiting
    allowed, reason = await rate_limiter.is_allowed(
        key=f"api_key:{api_key.id}",
        limit_per_minute=api_key.rate_limit_per_minute,
        limit_per_hour=api_key.rate_limit_per_hour
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason
        )
    
    # Обновление статистики использования
    api_key.last_used_at = datetime.now()
    api_key.total_requests += 1
    await db.commit()
    
    return api_key


def require_scope(required_scope: str):
    """
    Dependency для проверки наличия нужного scope
    
    Usage:
        @router.get("/users", dependencies=[Depends(require_scope("users:read"))])
    """
    async def scope_checker(api_key: APIKey = Depends(verify_api_key)):
        if not check_scope_permission(required_scope, api_key.scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scope: {required_scope}. Your scopes: {api_key.scopes}"
            )
        return api_key
    
    return scope_checker
