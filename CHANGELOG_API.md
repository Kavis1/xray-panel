# Changelog - External API & Optimization

## Version 1.1.0 (2025-10-06)

### 🚀 Новые функции

#### External API для внешних приложений
- **API ключи** с гранулярным контролем доступа (scopes)
- **RESTful API** для управления пользователями
- **Rate limiting** для предотвращения злоупотреблений
- **IP whitelist** для дополнительной безопасности
- **Автоматическое истечение** ключей

#### Endpoints

**API Keys Management:**
- `POST /api/v1/external/api-keys/` - Создать API ключ
- `GET /api/v1/external/api-keys/` - Список ключей
- `GET /api/v1/external/api-keys/{id}` - Детали ключа
- `PATCH /api/v1/external/api-keys/{id}` - Обновить ключ
- `POST /api/v1/external/api-keys/{id}/revoke` - Отозвать ключ
- `DELETE /api/v1/external/api-keys/{id}` - Удалить ключ
- `GET /api/v1/external/api-keys/scopes` - Доступные scopes

**Users API:**
- `POST /api/v1/external/users` - Создать пользователя
- `GET /api/v1/external/users` - Список пользователей (с пагинацией)
- `GET /api/v1/external/users/{username}` - Данные пользователя
- `PATCH /api/v1/external/users/{username}` - Обновить пользователя
- `DELETE /api/v1/external/users/{username}` - Удалить пользователя
- `GET /api/v1/external/users/{username}/subscription` - Ссылки подписки
- `GET /api/v1/external/users/{username}/traffic` - Статистика трафика
- `POST /api/v1/external/users/{username}/reset-traffic` - Сбросить трафик

### 🔒 Безопасность

#### Система Scopes
Детальный контроль прав доступа:
- `users:read` - Чтение данных пользователей
- `users:write` - Создание/обновление пользователей
- `users:delete` - Удаление пользователей
- `subscriptions:read` - Получение подписок
- `stats:read` - Просмотр статистики

Поддержка wildcards: `users:*`, `*:read`, `*:*`

#### Rate Limiting
- Настраиваемые лимиты per-minute и per-hour
- Автоматическая защита от DDOS
- Информативные заголовки о лимитах

#### Аутентификация
- API ключи с SHA256 хэшированием
- Невозможность восстановления (показывается один раз)
- Валидация формата: `xpanel_XXXX...`

### 📚 Документация

#### Новые файлы
- `backend/API_DOCUMENTATION.md` - Полная документация (10+ страниц)
- `EXTERNAL_API_QUICKSTART.md` - Быстрый старт (5 минут)
- Swagger UI с интерактивными примерами

#### Примеры кода
- Python (requests, httpx)
- JavaScript/Node.js (axios, fetch)
- cURL
- Полные рабочие примеры

### 🗄️ База данных

#### Новая таблица: `api_keys`
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    scopes JSON,
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    is_revoked BOOLEAN DEFAULT FALSE,
    allowed_ips JSON,
    expire_at DATETIME,
    last_used_at DATETIME,
    total_requests INTEGER DEFAULT 0,
    created_by_admin_id INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);
```

### 🔧 Технические детали

#### Новые модули
- `app/models/api_key.py` - SQLAlchemy модель
- `app/core/api_key_manager.py` - Генерация и проверка ключей
- `app/core/rate_limiter.py` - In-memory rate limiting
- `app/api/external_deps.py` - Dependencies для проверки
- `app/api/v1/endpoints/api_keys.py` - Управление ключами
- `app/api/v1/endpoints/external_users.py` - External Users API
- `app/api/v1/router_external.py` - Роутер

#### Миграция
- `alembic/versions/004_add_api_keys.py`

### 🎯 Use Cases

#### 1. Биллинг-система
```python
# Автоматическое создание пользователей при оплате
api.create_user(
    username=f"user_{order_id}",
    email=customer_email,
    traffic_limit_gb=purchased_gb,
    expire_days=purchased_days
)
```

#### 2. Telegram бот
```python
# Получение статистики для пользователя
traffic = api.get_user_traffic(username)
bot.send_message(f"Использовано: {traffic['traffic_used_gb']} ГБ")
```

#### 3. Мобильное приложение
```javascript
// Получение ссылок подписки
const links = await api.getUserSubscription(username);
showQRCode(links.universal_url);
```

### 📊 Производительность

- **Rate limiting:** До 1000 req/hour без блокировки
- **In-memory cache:** Минимальная задержка (<1ms)
- **Async/await:** Полная поддержка асинхронности
- **Пагинация:** Оптимизация больших выборок

### ⚡ Breaking Changes

Нет breaking changes. Все существующие API остаются работать.

### 🐛 Известные ограничения

- Rate limiter хранится в памяти (сбрасывается при рестарте)
- Для production рекомендуется Redis
- IP whitelist работает только для прямых подключений (не через proxy)

### 📝 Migration Guide

```bash
# 1. Применить миграцию
cd /root/panel/backend
source venv/bin/activate
alembic upgrade head

# 2. Перезапустить панель
systemctl restart xray-panel-api  # или
pkill -f uvicorn && nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 3. Создать первый API ключ
curl -X POST https://panel.example.com/api/v1/external/api-keys/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name": "My App", "scopes": ["users:*"]}'
```

### 🔮 Roadmap

#### Version 1.2.0
- [ ] Redis-based rate limiting
- [ ] Webhook notifications
- [ ] API usage analytics
- [ ] Bulk operations
- [ ] GraphQL endpoint

#### Version 1.3.0
- [ ] OAuth2 support
- [ ] API key rotation
- [ ] Advanced filtering
- [ ] Export/Import users
- [ ] API metrics dashboard

---

## Подробности

Полная документация: [API_DOCUMENTATION.md](./backend/API_DOCUMENTATION.md)  
Быстрый старт: [EXTERNAL_API_QUICKSTART.md](./EXTERNAL_API_QUICKSTART.md)  
Swagger UI: `https://YOUR_PANEL/docs`
