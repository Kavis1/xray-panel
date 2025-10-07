# Xray Panel API Documentation

## Обзор

Xray Panel предоставляет два типа API:

1. **Admin API** - для веб-интерфейса панели (требует JWT токен)
2. **External API** - для внешних приложений (требует API ключ)

---

## External API - Безопасный API для внешних приложений

### Аутентификация

External API использует API ключи для аутентификации. Все запросы должны включать заголовок:

```
Authorization: Bearer YOUR_API_KEY
```

### Получение API ключа

#### 1. Создание API ключа (только для администраторов)

```bash
POST /api/v1/external/api-keys/
Content-Type: application/json
Authorization: Bearer <ADMIN_JWT_TOKEN>

{
  "name": "My Application",
  "description": "API key for my app",
  "scopes": ["users:read", "users:write", "subscriptions:read"],
  "rate_limit_per_minute": 60,
  "rate_limit_per_hour": 1000,
  "allowed_ips": ["1.2.3.4"],  // опционально
  "expire_at": "2025-12-31T23:59:59"  // опционально
}
```

Ответ:
```json
{
  "id": 1,
  "name": "My Application",
  "api_key": "xpanel_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "scopes": ["users:read", "users:write", "subscriptions:read"],
  "rate_limit_per_minute": 60,
  "rate_limit_per_hour": 1000,
  "is_active": true,
  "created_at": "2025-10-06T10:00:00"
}
```

⚠️ **ВАЖНО:** API ключ показывается только один раз! Сохраните его в безопасном месте.

---

### Доступные Scopes

| Scope | Описание |
|-------|----------|
| `users:read` | Чтение данных пользователей |
| `users:write` | Создание и обновление пользователей |
| `users:delete` | Удаление пользователей |
| `subscriptions:read` | Получение ссылок подписки |
| `subscriptions:generate` | Генерация подписок |
| `nodes:read` | Чтение данных нод |
| `stats:read` | Просмотр статистики |

Поддерживаются wildcards:
- `users:*` - все операции с пользователями
- `*:read` - все операции чтения
- `*:*` - полный доступ (не рекомендуется)

---

## Endpoints - Управление пользователями

### 1. Создать пользователя

```bash
POST /api/v1/external/users
Authorization: Bearer xpanel_XXXXXXXX
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "traffic_limit_gb": 50,
  "expire_days": 30,
  "description": "Premium user",
  "protocols": ["vless", "vmess", "trojan"]
}
```

**Параметры:**
- `username` (обязательно) - Уникальное имя пользователя
- `email` (обязательно) - Email пользователя
- `traffic_limit_gb` (опционально) - Лимит трафика в ГБ (null = безлимит)
- `expire_days` (опционально) - Срок действия в днях
- `description` (опционально) - Описание пользователя
- `protocols` (опционально) - Список протоколов: vless, vmess, trojan, shadowsocks

**Ответ (201 Created):**
```json
{
  "id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "status": "active",
  "traffic_used_mb": 0.0,
  "traffic_limit_mb": 51200.0,
  "traffic_remaining_mb": 51200.0,
  "expire_at": "2025-11-05T10:00:00",
  "created_at": "2025-10-06T10:00:00",
  "subscription_url": "/api/v1/external/users/john_doe/subscription"
}
```

---

### 2. Получить список пользователей

```bash
GET /api/v1/external/users?skip=0&limit=50&status=active&search=john
Authorization: Bearer xpanel_XXXXXXXX
```

**Query параметры:**
- `skip` (по умолчанию: 0) - Пропустить N записей
- `limit` (по умолчанию: 50, макс: 200) - Максимум записей
- `status` (опционально) - Фильтр по статусу: active, disabled, limited, expired
- `search` (опционально) - Поиск по username или email

**Ответ (200 OK):**
```json
{
  "total": 150,
  "items": [
    {
      "id": 123,
      "username": "john_doe",
      "email": "john@example.com",
      "status": "active",
      "traffic_used_mb": 1250.5,
      "traffic_limit_mb": 51200.0,
      "traffic_remaining_mb": 49949.5,
      "expire_at": "2025-11-05T10:00:00",
      "created_at": "2025-10-06T10:00:00",
      "subscription_url": "/api/v1/external/users/john_doe/subscription"
    }
  ]
}
```

---

### 3. Получить данные пользователя

```bash
GET /api/v1/external/users/{username}
Authorization: Bearer xpanel_XXXXXXXX
```

**Ответ (200 OK):**
```json
{
  "id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "status": "active",
  "traffic_used_mb": 1250.5,
  "traffic_limit_mb": 51200.0,
  "traffic_remaining_mb": 49949.5,
  "expire_at": "2025-11-05T10:00:00",
  "created_at": "2025-10-06T10:00:00",
  "subscription_url": "/api/v1/external/users/john_doe/subscription"
}
```

---

### 4. Обновить пользователя

```bash
PATCH /api/v1/external/users/{username}
Authorization: Bearer xpanel_XXXXXXXX
Content-Type: application/json

{
  "email": "newemail@example.com",
  "traffic_limit_gb": 100,
  "extend_days": 30,
  "description": "VIP user",
  "status": "active"
}
```

**Параметры (все опциональны):**
- `email` - Новый email
- `traffic_limit_gb` - Новый лимит трафика в ГБ
- `extend_days` - Продлить на N дней
- `description` - Обновить описание
- `status` - Изменить статус: active, disabled, limited, expired

**Ответ (200 OK):**
```json
{
  "id": 123,
  "username": "john_doe",
  "email": "newemail@example.com",
  "status": "active",
  "traffic_used_mb": 1250.5,
  "traffic_limit_mb": 102400.0,
  "traffic_remaining_mb": 101149.5,
  "expire_at": "2025-12-05T10:00:00",
  "created_at": "2025-10-06T10:00:00",
  "subscription_url": "/api/v1/external/users/john_doe/subscription"
}
```

---

### 5. Удалить пользователя

```bash
DELETE /api/v1/external/users/{username}
Authorization: Bearer xpanel_XXXXXXXX
```

**Ответ (204 No Content)**

---

### 6. Получить ссылки подписки

```bash
GET /api/v1/external/users/{username}/subscription
Authorization: Bearer xpanel_XXXXXXXX
```

**Ответ (200 OK):**
```json
{
  "universal_url": "https://panel.example.com/sub/john_doe",
  "clash_url": "https://panel.example.com/sub/john_doe?format=clash",
  "singbox_url": "https://panel.example.com/sub/john_doe/singbox",
  "v2ray_url": "https://panel.example.com/sub/john_doe?format=v2ray"
}
```

---

### 7. Получить статистику трафика

```bash
GET /api/v1/external/users/{username}/traffic
Authorization: Bearer xpanel_XXXXXXXX
```

**Ответ (200 OK):**
```json
{
  "username": "john_doe",
  "traffic_used_bytes": 1311457280,
  "traffic_used_mb": 1250.5,
  "traffic_used_gb": 1.22,
  "traffic_limit_bytes": 53687091200,
  "traffic_limit_gb": 50.0,
  "traffic_remaining_gb": 48.78,
  "usage_percent": 2.44
}
```

---

### 8. Сбросить трафик пользователя

```bash
POST /api/v1/external/users/{username}/reset-traffic
Authorization: Bearer xpanel_XXXXXXXX
```

**Ответ (200 OK):**
```json
{
  "message": "Traffic reset for user 'john_doe'"
}
```

---

## Rate Limiting

Все запросы с API ключом подчиняются rate limiting:

- **По умолчанию:** 60 запросов в минуту, 1000 в час
- **Настраивается** при создании API ключа

При превышении лимита вы получите:
```json
HTTP 429 Too Many Requests
{
  "detail": "Rate limit exceeded: 60 requests per minute"
}
```

Заголовки ответа содержат информацию о лимитах:
```
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1696512345
```

---

## Коды ответов

| Код | Описание |
|-----|----------|
| 200 | OK - Запрос выполнен успешно |
| 201 | Created - Ресурс создан |
| 204 | No Content - Ресурс удален |
| 400 | Bad Request - Неверные параметры |
| 401 | Unauthorized - Неверный API ключ |
| 403 | Forbidden - Недостаточно прав (scopes) |
| 404 | Not Found - Ресурс не найден |
| 429 | Too Many Requests - Превышен лимит запросов |
| 500 | Internal Server Error - Внутренняя ошибка |

---

## Примеры использования

### Python

```python
import requests

API_KEY = "xpanel_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
BASE_URL = "https://panel.example.com/api/v1/external"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Создать пользователя
response = requests.post(
    f"{BASE_URL}/users",
    headers=headers,
    json={
        "username": "new_user",
        "email": "user@example.com",
        "traffic_limit_gb": 50,
        "expire_days": 30
    }
)

user = response.json()
print(f"Created user: {user['username']}")
print(f"Subscription: {user['subscription_url']}")

# Получить статистику
response = requests.get(
    f"{BASE_URL}/users/new_user/traffic",
    headers=headers
)

traffic = response.json()
print(f"Traffic used: {traffic['traffic_used_gb']:.2f} GB")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_KEY = 'xpanel_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';
const BASE_URL = 'https://panel.example.com/api/v1/external';

const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
};

// Создать пользователя
async function createUser() {
    const response = await axios.post(`${BASE_URL}/users`, {
        username: 'new_user',
        email: 'user@example.com',
        traffic_limit_gb: 50,
        expire_days: 30
    }, { headers });
    
    console.log('Created user:', response.data.username);
    console.log('Subscription:', response.data.subscription_url);
}

// Получить список пользователей
async function listUsers() {
    const response = await axios.get(`${BASE_URL}/users?limit=10`, { headers });
    
    console.log(`Total users: ${response.data.total}`);
    response.data.items.forEach(user => {
        console.log(`- ${user.username}: ${user.traffic_used_mb} MB used`);
    });
}

createUser();
listUsers();
```

### cURL

```bash
# Создать пользователя
curl -X POST "https://panel.example.com/api/v1/external/users" \
  -H "Authorization: Bearer xpanel_XXXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "email": "user@example.com",
    "traffic_limit_gb": 50,
    "expire_days": 30
  }'

# Получить список пользователей
curl -X GET "https://panel.example.com/api/v1/external/users?limit=10" \
  -H "Authorization: Bearer xpanel_XXXXXXXX"

# Обновить пользователя
curl -X PATCH "https://panel.example.com/api/v1/external/users/john_doe" \
  -H "Authorization: Bearer xpanel_XXXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "extend_days": 30,
    "traffic_limit_gb": 100
  }'

# Получить статистику
curl -X GET "https://panel.example.com/api/v1/external/users/john_doe/traffic" \
  -H "Authorization: Bearer xpanel_XXXXXXXX"
```

---

## Безопасность

### Рекомендации

1. **Храните API ключи в безопасности** - никогда не публикуйте их в публичных репозиториях
2. **Используйте HTTPS** - всегда используйте шифрованное соединение
3. **Ограничьте IP адреса** - настройте `allowed_ips` для дополнительной защиты
4. **Минимальные права** - создавайте API ключи только с необходимыми scopes
5. **Ротация ключей** - регулярно обновляйте API ключи
6. **Мониторинг** - следите за `total_requests` и `last_used_at`
7. **Срок действия** - устанавливайте `expire_at` для временных ключей

### IP Whitelist

Ограничьте доступ к API только с определенных IP:

```json
{
  "name": "Production Server",
  "allowed_ips": ["1.2.3.4", "5.6.7.8"],
  "scopes": ["users:*"]
}
```

---

## Swagger UI

Интерактивная документация API доступна по адресу:

```
https://panel.example.com/docs
```

Здесь вы можете:
- Просмотреть все endpoints
- Протестировать запросы
- Увидеть примеры ответов
- Изучить схемы данных

---

## Поддержка

При возникновении проблем:

1. Проверьте логи панели: `/tmp/panel.log`
2. Проверьте формат API ключа: должен начинаться с `xpanel_`
3. Убедитесь что у API ключа есть нужные scopes
4. Проверьте rate limiting
5. Проверьте IP whitelist

---

## Changelog

### Version 1.0.0 (2025-10-06)
- Первый релиз External API
- Поддержка API ключей с scopes
- Rate limiting
- IP whitelist
- CRUD операции для пользователей
- Получение подписок
- Статистика трафика
