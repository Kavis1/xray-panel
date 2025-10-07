# External API - Быстрый старт

## 1. Создайте API ключ

Войдите в панель как администратор и выполните:

```bash
curl -X POST "https://YOUR_PANEL_URL/api/v1/external/api-keys/" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "scopes": ["users:read", "users:write", "subscriptions:read"],
    "rate_limit_per_minute": 60
  }'
```

**Сохраните полученный API ключ!** Он показывается только один раз.

## 2. Используйте API

### Создать пользователя

```bash
curl -X POST "https://YOUR_PANEL_URL/api/v1/external/users" \
  -H "Authorization: Bearer xpanel_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "traffic_limit_gb": 50,
    "expire_days": 30
  }'
```

### Получить список пользователей

```bash
curl "https://YOUR_PANEL_URL/api/v1/external/users?limit=10" \
  -H "Authorization: Bearer xpanel_YOUR_API_KEY"
```

### Получить ссылку подписки

```bash
curl "https://YOUR_PANEL_URL/api/v1/external/users/newuser/subscription" \
  -H "Authorization: Bearer xpanel_YOUR_API_KEY"
```

## 3. Python пример

```python
import requests

API_KEY = "xpanel_YOUR_API_KEY"
BASE_URL = "https://YOUR_PANEL_URL/api/v1/external"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Создать пользователя
user = requests.post(
    f"{BASE_URL}/users",
    headers=headers,
    json={
        "username": "newuser",
        "email": "user@example.com",
        "traffic_limit_gb": 50,
        "expire_days": 30
    }
).json()

print(f"User created: {user['username']}")
print(f"Subscription URL: {user['subscription_url']}")
```

## Полная документация

Смотрите [API_DOCUMENTATION.md](./backend/API_DOCUMENTATION.md) для подробной информации.

## Swagger UI

Интерактивная документация: `https://YOUR_PANEL_URL/docs`
