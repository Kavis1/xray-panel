# Xray Панель Управления

Комплексная система управления multi-node прокси на базе Xray-core с поддержкой протоколов VMess, VLESS, Trojan, Shadowsocks, Hysteria и Hysteria2.

## Возможности

### Основные функции
- **Поддержка множества протоколов**: VMess, VLESS, Trojan, Shadowsocks, Hysteria, Hysteria2
- **Multi-node архитектура**: Распределённое управление инфраструктурой
- **Управление трафиком**: Квоты, истечение срока, периодические сбросы
- **Генерация подписок**: Форматы V2Ray, Clash, Clash Meta, Sing-box, Outline
- **Ограничение устройств по HWID**: Контроль доступа устройств на пользователя
- **Статистика в реальном времени**: Мониторинг трафика, онлайн пользователи, метрики системы
- **Webhook уведомления**: Настраиваемые уведомления о событиях с HMAC подписями
- **Telegram бот**: Управление пользователями и уведомления (опционально)
- **REST API**: Полный API с документацией OpenAPI
- **CLI/TUI**: Интерфейс командной строки для администрирования

### Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Панель управления                         │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │  Web UI    │  │  REST API   │  │  Сервис подписок     │  │
│  │  (React)   │  │  (FastAPI)  │  │                      │  │
│  └────────────┘  └─────────────┘  └──────────────────────┘  │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │  Telegram  │  │  Webhooks   │  │  Фоновые задачи      │  │
│  │  бот       │  │  Gateway    │  │  (Celery)            │  │
│  └────────────┘  └─────────────┘  └──────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL + Redis                                    │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                    gRPC/REST (TLS)
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                        Нода (Node Plane)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Node Service   │  │  Node Service   │  │  Node ...    │ │
│  │  (Go gRPC/REST) │  │  (Go gRPC/REST) │  │              │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘ │
│           │                    │                   │         │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌──────▼───────┐ │
│  │  Xray-core      │  │  Xray-core      │  │  Xray-core   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Быстрый старт

### Использование Docker Compose (Рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-repo/xray-panel.git
cd xray-panel
```

2. Настройте окружение:
```bash
cp backend/.env.example backend/.env
# Отредактируйте backend/.env с вашими настройками
```

3. Запустите сервисы:
```bash
cd docker
docker-compose up -d
```

4. Доступ к панели:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API: http://localhost:8000

5. Создайте первого администратора:
```bash
docker-compose exec backend python -m app.cli admin create \
  --username admin \
  --password ваш_безопасный_пароль \
  --sudo
```

### Ручная установка

#### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env

# Выполните миграции
alembic upgrade head

# Создайте админа
python -m app.cli admin create --username admin --password pass --sudo

# Запустите сервер
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Сервис ноды

```bash
cd node
go mod download
cp .env.example .env
# Отредактируйте .env

# Соберите и запустите
go build -o node cmd/main.go
./node
```

## Документация

### API Документация

После запуска доступна по адресу `/docs` для интерактивной документации API (Swagger UI).

### Структура проекта

```
panel/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # REST API endpoints
│   │   ├── models/    # Модели базы данных
│   │   ├── schemas/   # Pydantic схемы
│   │   ├── services/  # Бизнес-логика
│   │   └── core/      # Конфигурация
│   └── alembic/       # Миграции БД
├── node/              # Go сервис ноды
│   ├── cmd/           # Главное приложение
│   ├── pkg/           # Пакеты
│   │   ├── api/       # gRPC/REST обработчики
│   │   ├── xray/      # Менеджер Xray
│   │   └── stats/     # Сборщик статистики
│   └── proto/         # Protobuf определения
├── frontend/          # React frontend
├── docker/            # Docker конфигурации
└── docs/              # Документация
```

## Конфигурация

### Переменные окружения Backend

```env
# База данных
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/panel

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
SECRET_KEY=ваш-секретный-ключ
JWT_ALGORITHM=HS256

# Подписки
XRAY_SUBSCRIPTION_URL_PREFIX=https://panel.example.com/sub

# HWID
HWID_DEVICE_LIMIT_ENABLED=true
HWID_FALLBACK_DEVICE_LIMIT=3

# Webhooks
WEBHOOK_SECRET_HEADER=ваш-webhook-секрет

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=ваш-токен-бота
TELEGRAM_ADMIN_IDS=[123456789]
```

### Переменные окружения сервиса ноды

```env
SERVICE_PORT=50051
SERVICE_PROTOCOL=grpc
NODE_HOST=0.0.0.0
XRAY_EXECUTABLE_PATH=/usr/local/bin/xray
XRAY_ASSETS_PATH=/usr/local/share/xray
API_KEY=ваш-ключ-api-ноды
SSL_CERT_FILE=  # Опционально
SSL_KEY_FILE=   # Опционально
```

## Примеры использования

### Создание пользователя

```bash
# Через CLI
panel user add alice --expire 2025-12-31 --traffic 50GB

# Через API
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "expire_at": "2025-12-31T23:59:59Z",
    "traffic_limit_bytes": 53687091200,
    "traffic_limit_strategy": "MONTH"
  }'
```

### Добавление ноды

```bash
# Через CLI
panel node add ru-node-1 \
  --address node1.example.com \
  --api-port 50051 \
  --api-key секрет \
  --usage-ratio 1.0

# Через API
curl -X POST http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "ru-node-1",
    "address": "node1.example.com",
    "api_port": 50051,
    "api_key": "секрет",
    "usage_ratio": 1.0
  }'
```

### Получение подписки

```
https://panel.example.com/sub/alice
```

Поддерживается автоопределение типа клиента или явный формат:
- `/sub/alice/clash` - Clash YAML
- `/sub/alice/singbox` - Sing-box JSON  
- `/sub/alice/raw` - V2Ray base64

## Разработка

### Запуск тестов

```bash
cd backend
pytest
```

### Миграции базы данных

```bash
# Создать миграцию
alembic revision --autogenerate -m "описание"

# Применить миграции
alembic upgrade head

# Откатить
alembic downgrade -1
```

### Генерация Protobuf

```bash
cd node
protoc --go_out=. --go-grpc_out=. proto/node.proto
```

## Безопасность

- Вся связь между Панелью и Нодами использует TLS (опционально)
- API ключи для аутентификации нод
- JWT токены для аутентификации администраторов
- HMAC верификация подписей для webhooks
- Ограничение частоты запросов к API
- CORS конфигурация
- Аудит логирование

## Вклад в проект

Вклад приветствуется! Пожалуйста, прочитайте наши руководства по участию и отправляйте pull requests.

## Лицензия

[Ваша лицензия здесь]

## Поддержка

- Документация: [Ссылка на документацию]
- Проблемы: [GitHub Issues]
- Telegram: [Telegram группа]

## Благодарности

Создано с вдохновением от:
- [Marzban](https://github.com/Gozargah/Marzban)
- [PasarGuard](https://github.com/PasarGuard/panel)
- [Remnawave](https://github.com/remnawave/panel)
