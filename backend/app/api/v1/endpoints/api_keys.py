from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.admin import Admin
from app.models.api_key import APIKey
from app.api.deps import get_current_admin, get_current_sudo_admin
from app.core.api_key_manager import generate_api_key, APIKeyScopes
from pydantic import BaseModel, Field

router = APIRouter()


# Schemas
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Название API ключа")
    description: Optional[str] = Field(None, description="Описание назначения ключа")
    scopes: List[str] = Field(..., description="Список разрешений (scopes)")
    rate_limit_per_minute: Optional[int] = Field(60, ge=1, le=1000, description="Лимит запросов в минуту")
    rate_limit_per_hour: Optional[int] = Field(1000, ge=1, le=100000, description="Лимит запросов в час")
    allowed_ips: Optional[List[str]] = Field(None, description="Список разрешенных IP адресов")
    expire_at: Optional[datetime] = Field(None, description="Дата истечения ключа")


class APIKeyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    scopes: List[str]
    rate_limit_per_minute: Optional[int]
    rate_limit_per_hour: Optional[int]
    is_active: bool
    is_revoked: bool
    allowed_ips: Optional[List[str]]
    expire_at: Optional[datetime]
    last_used_at: Optional[datetime]
    total_requests: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    api_key: str = Field(..., description="API ключ (показывается только при создании!)")


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    allowed_ips: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.get("/scopes", response_model=List[str])
async def get_available_scopes(
    current_admin: Admin = Depends(get_current_admin),
):
    """
    Получить список всех доступных scopes
    
    Scopes определяют какие операции может выполнять API ключ:
    - users:read - Чтение данных пользователей
    - users:write - Создание и обновление пользователей
    - users:delete - Удаление пользователей
    - subscriptions:read - Получение подписок
    - nodes:read - Чтение данных нод
    - stats:read - Просмотр статистики
    
    Поддерживаются wildcards:
    - users:* - Все операции с пользователями
    - *:read - Все read операции
    """
    return APIKeyScopes.all_scopes()


@router.post("/", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    """
    Создать новый API ключ
    
    **ВАЖНО:** API ключ показывается только один раз при создании!
    Сохраните его в безопасном месте.
    
    **Пример использования:**
    ```
    curl -H "Authorization: Bearer YOUR_API_KEY" https://panel.example.com/api/v1/external/users
    ```
    """
    # Проверка корректности scopes
    if not APIKeyScopes.validate_scopes(key_data.scopes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scopes. Use /api-keys/scopes to get available scopes."
        )
    
    # Генерация API ключа
    api_key, key_hash = generate_api_key()
    
    # Создание записи в БД
    new_key = APIKey(
        key_hash=key_hash,
        name=key_data.name,
        description=key_data.description,
        scopes=key_data.scopes,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        allowed_ips=key_data.allowed_ips,
        expire_at=key_data.expire_at,
        created_by_admin_id=current_admin.id,
    )
    
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    # Возвращаем ключ с секретом
    response = APIKeyWithSecret.model_validate(new_key)
    response.api_key = api_key
    
    return response


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    show_revoked: bool = False,
):
    """Получить список всех API ключей"""
    query = select(APIKey).order_by(APIKey.created_at.desc())
    
    if not show_revoked:
        query = query.where(APIKey.is_revoked == False)
    
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    return api_keys


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Получить информацию об API ключе"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return api_key


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    update_data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    """Обновить API ключ"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Обновление полей
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if 'scopes' in update_dict and update_dict['scopes']:
        if not APIKeyScopes.validate_scopes(update_dict['scopes']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid scopes"
            )
    
    for key, value in update_dict.items():
        setattr(api_key, key, value)
    
    await db.commit()
    await db.refresh(api_key)
    
    return api_key


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    """
    Отозвать API ключ
    
    Отозванный ключ больше не сможет выполнять запросы
    """
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_revoked = True
    api_key.is_active = False
    
    await db.commit()
    
    return {"message": "API key revoked successfully"}


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    """Удалить API ключ"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    await db.delete(api_key)
    await db.commit()
