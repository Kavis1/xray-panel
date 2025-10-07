import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List


def generate_api_key() -> tuple[str, str]:
    """
    Генерация API ключа
    
    Returns:
        (api_key, key_hash) - ключ для пользователя и хэш для базы данных
    """
    # Генерируем случайный ключ (64 символа)
    api_key = f"xpanel_{secrets.token_urlsafe(48)}"
    
    # Создаем хэш для хранения в БД
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, key_hash


def hash_api_key(api_key: str) -> str:
    """Хэширование API ключа"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key_format(api_key: str) -> bool:
    """Проверка формата API ключа"""
    return api_key.startswith("xpanel_") and len(api_key) > 50


class APIKeyScopes:
    """Список доступных скоупов для API ключей"""
    
    # Пользователи
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    
    # Подписки
    SUBSCRIPTIONS_READ = "subscriptions:read"
    SUBSCRIPTIONS_GENERATE = "subscriptions:generate"
    
    # Ноды
    NODES_READ = "nodes:read"
    NODES_WRITE = "nodes:write"
    NODES_CONTROL = "nodes:control"
    
    # Inbounds
    INBOUNDS_READ = "inbounds:read"
    INBOUNDS_WRITE = "inbounds:write"
    
    # Статистика
    STATS_READ = "stats:read"
    
    # Системные
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    
    @classmethod
    def all_scopes(cls) -> List[str]:
        """Получить все доступные скоупы"""
        return [
            value for key, value in cls.__dict__.items()
            if not key.startswith('_') and isinstance(value, str) and ':' in value
        ]
    
    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> bool:
        """Проверка корректности скоупов"""
        valid_scopes = cls.all_scopes()
        return all(scope in valid_scopes for scope in scopes)


def check_scope_permission(required_scope: str, api_key_scopes: List[str]) -> bool:
    """
    Проверка наличия требуемого скоупа
    
    Поддерживает wildcard:
    - users:* даёт доступ к users:read, users:write, users:delete
    - *:read даёт доступ ко всем read операциям
    """
    if not api_key_scopes:
        return False
    
    # Проверка точного совпадения
    if required_scope in api_key_scopes:
        return True
    
    # Проверка wildcard
    resource, action = required_scope.split(':')
    
    # users:* позволяет все операции с users
    if f"{resource}:*" in api_key_scopes:
        return True
    
    # *:read позволяет все read операции
    if f"*:{action}" in api_key_scopes:
        return True
    
    # *:* даёт полный доступ
    if "*:*" in api_key_scopes:
        return True
    
    return False
