# Руководство по быстрому запуску

Это руководство поможет вам запустить Xray Panel за считанные минуты.

## Предварительные требования

- Docker и Docker Compose (рекомендуется)
- ИЛИ: Python 3.11+, PostgreSQL, Redis (ручная установка)
- Root или sudo доступ
- Открытые порты: 80, 443, 8000 (панель), 50051 (нода)

## Методы установки

### Вариант 1: Docker Compose (Рекомендуется)

#### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your-repo/xray-panel.git
cd xray-panel
```

#### Шаг 2: Настройка окружения

```bash
# Скопируйте файл окружения
cp backend/.env.example backend/.env

# Сгенерируйте секретный ключ
SECRET_KEY=$(openssl rand -hex 32)

# Отредактируйте .env и установите SECRET_KEY
nano backend/.env
```

Минимальные необходимые настройки в `.env`:
```env
DATABASE_URL=postgresql+asyncpg://panel:panel_password@postgres:5432/panel
REDIS_URL=redis://redis:6379/0
SECRET_KEY=ваш-сгенерированный-секретный-ключ
XRAY_SUBSCRIPTION_URL_PREFIX=https://ваш-домен.com/sub
```

#### Шаг 3: Запуск сервисов

```bash
cd docker
docker-compose up -d
```

Это запустит:
- PostgreSQL база данных
- Redis кеш
- Backend API (порт 8000)
- Celery worker
- Frontend (порт 3000)
- Nginx обратный прокси (порт 80)

#### Шаг 4: Инициализация базы данных

```bash
docker-compose exec backend alembic upgrade head
```

#### Шаг 5: Создание администратора

```bash
docker-compose exec backend python -m app.cli admin create \
  --username admin \
  --password ВашБезопасныйПароль123 \
  --sudo
```

#### Шаг 6: Доступ к панели

- **Frontend**: http://localhost (или ваш домен)
- **API Docs**: http://localhost/docs
- **Вход**: Используйте учётные данные из Шага 5

### Вариант 2: Ручная установка

#### Шаг 1: Установка системных зависимостей

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql redis-server nginx git
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip postgresql-server redis nginx git
```

#### Шаг 2: Установка Xray-core

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

#### Шаг 3: Настройка панели

```bash
# Создайте директорию установки
sudo mkdir -p /opt/xray-panel
cd /opt/xray-panel

# Клонируйте репозиторий
git clone https://github.com/your-repo/xray-panel.git .

# Настройте Python окружение
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Шаг 4: Настройка базы данных

```bash
# Создайте базу данных и пользователя
sudo -u postgres psql << EOF
CREATE USER panel WITH PASSWORD 'ваш_пароль';
CREATE DATABASE panel OWNER panel;
\q
EOF
```

#### Шаг 5: Настройка панели

```bash
# Скопируйте и отредактируйте окружение
cp .env.example .env
nano .env
```

Обновите эти значения:
```env
DATABASE_URL=postgresql+asyncpg://panel:ваш_пароль@localhost:5432/panel
SECRET_KEY=$(openssl rand -hex 32)
XRAY_SUBSCRIPTION_URL_PREFIX=https://ваш-домен.com/sub
```

#### Шаг 6: Выполнение миграций

```bash
alembic upgrade head
```

#### Шаг 7: Создание администратора

```bash
python -m app.cli admin create --username admin --password pass --sudo
```

#### Шаг 8: Запуск сервисов

```bash
# Backend API
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Worker
celery -A app.workers.celery worker --loglevel=info &
```

Для продакшена используйте systemd (см. скрипт установки).

## Добавление вашей первой ноды

### На сервере ноды

#### Вариант 1: Docker

```bash
# Создайте директорию ноды
mkdir -p ~/xray-node
cd ~/xray-node

# Скопируйте файлы ноды и соберите
docker build -t xray-node -f /path/to/panel/node/Dockerfile .

# Сгенерируйте API ключ
API_KEY=$(openssl rand -hex 32)

# Запустите контейнер
docker run -d \
  -e SERVICE_PORT=50051 \
  -e API_KEY=$API_KEY \
  -p 50051:50051 \
  --name xray-node \
  xray-node
```

#### Вариант 2: Вручную

```bash
# Запустите скрипт установки
sudo bash /path/to/panel/scripts/install-node.sh

# Или вручную:
# 1. Установите Xray-core
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# 2. Установите Go и соберите ноду
cd /opt/xray-panel-node
go mod download
go build -o node cmd/main.go

# 3. Настройте
cp .env.example .env
# Отредактируйте .env и установите API_KEY

# 4. Запустите сервис
./node
```

### В UI панели

1. Войдите в панель
2. Перейдите на страницу **Ноды**
3. Нажмите **Добавить ноду**
4. Заполните детали:
   - Имя: `node-1`
   - Адрес: `ip-сервера-ноды`
   - API порт: `50051`
   - Протокол: `grpc`
   - API ключ: (ключ сгенерированный выше)
   - Usage Ratio: `1.0`
5. Нажмите **Подключить**

## Создание первого пользователя

### Через Web UI

1. Перейдите на страницу **Пользователи**
2. Нажмите **Добавить пользователя**
3. Заполните:
   - Имя пользователя: `alice`
   - Лимит трафика: `50 GB`
   - Истечение: `2025-12-31`
4. Добавьте прокси (VLESS, VMess и т.д.)
5. Назначьте на inbound'ы
6. Сохраните

### Через CLI

```bash
docker-compose exec backend python -m app.cli user add \
  --username alice \
  --traffic 50 \
  --expire 2025-12-31
```

### Через API

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer ВАШ_ТОКЕН" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "traffic_limit_bytes": 53687091200,
    "expire_at": "2025-12-31T23:59:59Z"
  }'
```

## Создание Inbound'ов

### VLESS с Reality

```bash
# В UI панели, перейдите в Inbound'ы → Добавить Inbound

Tag: vless-reality
Type: VLESS
Port: 443
Network: tcp
Security: reality

Настройки Reality:
{
  "serverNames": ["cdn.cloudflare.com"],
  "privateKey": "ваш-приватный-ключ",
  "shortIds": ["a1b2c3"],
  "fingerprint": "chrome"
}
```

Сгенерируйте Reality ключи:
```bash
xray x25519
```

### VMess с WebSocket

```
Tag: vmess-ws
Type: VMESS
Port: 8080
Network: ws
Security: none

Настройки Stream:
{
  "ws": {
    "path": "/vmess"
  }
}
```

## Получение подписки пользователя

После создания пользователя и назначения на inbound'ы:

```
https://ваш-домен.com/sub/alice
```

Автоматически определяет тип клиента, или укажите формат:
- `/sub/alice/clash` - Clash YAML
- `/sub/alice/singbox` - Sing-box JSON
- `/sub/alice/raw` - V2Ray ссылки

## Мониторинг

### Проверка статуса системы

```bash
# Docker
docker-compose ps
docker-compose logs -f backend

# Вручную
systemctl status xray-panel
systemctl status xray-panel-worker
```

### Просмотр логов

```bash
# Логи Backend
docker-compose logs -f backend

# Логи Worker
docker-compose logs -f worker

# Логи Node
docker logs xray-node
```

### Панель управления

Войдите в панель и проверьте Dashboard для:
- Общее количество пользователей
- Активные ноды
- Статистика трафика
- Онлайн пользователи

## Распространённые операции

### Перезапуск сервисов

```bash
# Docker
docker-compose restart backend worker

# Вручную
sudo systemctl restart xray-panel xray-panel-worker
```

### Обновление панели

```bash
cd /path/to/panel
git pull
docker-compose down
docker-compose up -d --build
```

### Резервное копирование базы данных

```bash
docker-compose exec postgres pg_dump -U panel panel > backup.sql
```

### Восстановление базы данных

```bash
docker-compose exec -T postgres psql -U panel panel < backup.sql
```

## Устранение неполадок

### Панель недоступна

Проверьте запущены ли сервисы:
```bash
docker-compose ps
```

Проверьте логи:
```bash
docker-compose logs backend
```

### Нода не подключается

1. Проверьте что firewall разрешает порт 50051
2. Проверьте что API ключи совпадают
3. Проверьте логи ноды
4. Проверьте подключение: `curl http://ip-ноды:50051/info`

### Пользователи не могут подключиться

1. Проверьте конфигурацию inbound
2. Проверьте что порты открыты
3. Проверьте что Xray работает на ноде
4. Проверьте URL подписки

### Ошибки базы данных

Убедитесь что база данных доступна:
```bash
docker-compose exec postgres psql -U panel -d panel -c "SELECT 1;"
```

## Рекомендации по безопасности

1. **Используйте сложные пароли** для учётных записей администраторов
2. **Включите HTTPS** с валидными SSL сертификатами
3. **Используйте firewall** для ограничения доступа к портам управления
4. **Регулярные резервные копии** базы данных
5. **Держите софт обновлённым**
6. **Мониторьте логи** на подозрительную активность
7. **Используйте разные API ключи** для каждой ноды
8. **Включите MFA** для учётных записей администраторов (если доступно)

## Следующие шаги

- Настройте webhooks для уведомлений
- Настройте Telegram бота (опционально)
- Настройте лимиты трафика
- Настройте автоматические резервные копии
- Добавьте больше нод
- Настройте конфигурации inbound
- Настройте мониторинг и оповещения

## Получение помощи

- Документация: /docs
- API справка: /api/v1/docs
- GitHub Issues: [ссылка]
- Telegram группа: [ссылка]

## Чеклист для продакшена

Перед выходом в продакшен:

- [ ] Используйте сильный SECRET_KEY
- [ ] Настройте SSL/TLS сертификаты
- [ ] Настройте правила firewall
- [ ] Настройте резервное копирование БД
- [ ] Включите мониторинг
- [ ] Настройте webhooks
- [ ] Протестируйте сценарии отказа
- [ ] Задокументируйте вашу настройку
- [ ] Настройте ротацию логов
- [ ] Настройте ограничение частоты запросов
- [ ] Проверьте настройки безопасности
- [ ] Настройте оповещения
