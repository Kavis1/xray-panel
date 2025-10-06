# Xray Panel - Deployment

Автоматическая установка панели управления и нод для Xray VPN.

## Компоненты

### 📊 Панель управления
- REST API (FastAPI)
- Web интерфейс
- База данных (SQLite/PostgreSQL)
- Автоматический сбор статистики
- SSL сертификаты (Let's Encrypt)

### 🌍 Ноды
- Поддержка протоколов: VLESS, VMess, Trojan, Shadowsocks, Hysteria2
- Автоматическая синхронизация с панелью
- Сбор трафика и статистики
- gRPC API для управления

## Быстрый старт

### Установка панели

```bash
# Скачать и установить панель
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh
chmod +x install.sh
sudo ./install.sh
```

Требуется:
- Домен с A-записью на IP сервера
- Email для SSL сертификата

[Подробная инструкция →](./panel/README.md)

### Установка ноды

```bash
# Скачать и установить ноду
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/node/install-node.sh
chmod +x install-node.sh
sudo ./install-node.sh
```

После установки скопируйте данные подключения и добавьте ноду в панель.

[Подробная инструкция →](./node/README.md)

## Архитектура

```
                    ┌─────────────────┐
                    │   Web Browser   │
                    └────────┬────────┘
                             │ HTTPS
                    ┌────────▼────────┐
                    │     Nginx       │
                    │   (SSL/Proxy)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│  Panel API    │   │  Celery Beat  │   │ Celery Worker │
│   (FastAPI)   │   │  (Scheduler)  │   │   (Stats)     │
└───────┬───────┘   └───────────────┘   └───────┬───────┘
        │                                        │
        │           ┌────────────────────────────┘
        │           │
        │    ┌──────▼──────┐       ┌──────────────┐
        │    │  Database   │◄──────┤    Redis     │
        │    │ (SQLite/PG) │       │   (Broker)   │
        │    └─────────────┘       └──────────────┘
        │
        │  gRPC :50051
        │
┌───────▼─────────────────────────────────────────┐
│                    Nodes                        │
├─────────────────┬───────────────┬───────────────┤
│   Node 1 (DE)   │  Node 2 (US)  │  Node 3 (SG)  │
├─────────────────┼───────────────┼───────────────┤
│ • Xray          │ • Xray        │ • Xray        │
│ • sing-box      │ • sing-box    │ • sing-box    │
│ • Node Service  │ • Node Service│ • Node Service│
└─────────────────┴───────────────┴───────────────┘
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │  Users  │      │  Users  │     │  Users  │
    └─────────┘      └─────────┘     └─────────┘
```

## Возможности

### ✅ Управление пользователями
- Создание/удаление/редактирование
- Ограничения трафика
- Ограничения скорости
- Срок действия
- Блокировка торрентов

### ✅ Множественные протоколы
- VLESS (Reality, WebSocket, gRPC)
- VMess (WebSocket, gRPC)
- Trojan (TCP, WebSocket)
- Shadowsocks
- Hysteria2

### ✅ Автоматический сбор статистики
- Трафик каждого пользователя (Xray + sing-box)
- Трафик нод (суммарный)
- Статус нод (online/offline)
- Версии Xray на нодах
- Обновление каждые 5 минут

### ✅ Управление нодами
- Подключение нод по gRPC
- Автоматическая синхронизация конфигов
- Привязка пользователей к нодам
- Мониторинг состояния

### ✅ Безопасность
- SSL сертификаты (Let's Encrypt)
- API ключи для нод
- JWT токены для админов
- Аудит действий

### ✅ API и интеграции
- REST API (FastAPI)
- Автоматическая документация (Swagger)
- Webhook уведомления
- Telegram бот (опционально)

## Технологии

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy (ORM)
- Alembic (миграции)
- Celery (фоновые задачи)
- Redis (брокер)

### Proxy
- Xray-core (основной прокси)
- sing-box (Hysteria)
- gRPC (связь с нодами)

### Frontend (опционально)
- React + TypeScript
- TailwindCSS
- API клиент

## Системные требования

### Панель
- **RAM:** 1GB+ (рекомендуется 2GB)
- **CPU:** 1 core (рекомендуется 2)
- **Диск:** 10GB+
- **ОС:** Ubuntu 20.04+, Debian 11+, CentOS 8+

### Нода
- **RAM:** 512MB+ (рекомендуется 1GB)
- **CPU:** 1 core
- **Диск:** 5GB+
- **ОС:** Ubuntu 20.04+, Debian 11+, CentOS 8+

## Типичные сценарии

### 1. Одиночный сервер
Панель и нода на одном сервере (для тестирования или малого проекта).

```bash
# Установите панель
sudo ./install.sh

# Нода создается автоматически на localhost
```

### 2. Панель + удалённые ноды
Панель на одном сервере, ноды на разных серверах в разных странах.

```bash
# Сервер 1: Установите панель
sudo ./install.sh

# Сервер 2 (DE): Установите ноду
sudo ./install-node.sh

# Сервер 3 (US): Установите ноду
sudo ./install-node.sh

# Добавьте ноды в панель через Web UI
```

### 3. Высоконагруженная система
Несколько нод, PostgreSQL, мониторинг.

```bash
# Установите панель с PostgreSQL
sudo ./install.sh  # выберите PostgreSQL

# Установите ноды в разных локациях
# Настройте мониторинг (Prometheus, Grafana)
```

## Мониторинг

### Проверка сервисов панели
```bash
systemctl status xray-panel-api
systemctl status celery-worker
systemctl status celery-beat
journalctl -u celery-worker -f
```

### Проверка сервисов ноды
```bash
systemctl status xray-panel-node
systemctl status xray-node
systemctl status singbox-node
```

### Проверка сбора трафика
```bash
# Панель
journalctl -u celery-worker | grep "Updated"

# Нода
xray api statsquery --server=127.0.0.1:10085 -pattern="user>>>"
curl http://127.0.0.1:9090/connections
```

## Обновление

### Панель
```bash
cd /opt/xray-panel
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart xray-panel-api celery-worker celery-beat
```

### Нода
```bash
cd /opt/xray-panel-node
git pull
/usr/local/go/bin/go build -o xray-panel-node cmd/main.go
systemctl restart xray-panel-node
```

## Резервное копирование

### Автоматический backup панели
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

# База данных
cp /opt/xray-panel/backend/panel.db "$BACKUP_DIR/panel_$DATE.db"

# Конфигурация
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/xray-panel/backend/.env

# Удаление старых (старше 30 дней)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Добавьте в crontab:
```bash
0 2 * * * /root/backup.sh
```

## Безопасность

### Рекомендации для панели
1. ✅ Используйте сложный пароль админа
2. ✅ Регулярно обновляйте систему
3. ✅ Настройте firewall (только 80, 443, SSH)
4. ✅ Используйте SSH ключи вместо паролей
5. ✅ Регулярно делайте backup

### Рекомендации для нод
1. ✅ Храните API ключи в секрете
2. ✅ Ограничьте gRPC порт (только IP панели)
3. ✅ Регулярно обновляйте Xray и sing-box
4. ✅ Мониторьте использование ресурсов

## Решение проблем

### Панель не запускается
```bash
journalctl -u xray-panel-api -n 100
cat /tmp/panel.log
```

### Трафик не собирается
```bash
# Проверьте Celery
systemctl status celery-worker celery-beat
journalctl -u celery-worker -f

# Проверьте Redis
systemctl status redis-server
redis-cli ping
```

### Нода не подключается
```bash
# На ноде
journalctl -u xray-panel-node -n 50

# Проверьте сеть
telnet IP_ПАНЕЛИ 50051

# Проверьте API ключ
cat /opt/xray-panel-node/.env
```

### SSL не работает
```bash
# Проверьте DNS
dig +short ваш-домен

# Получите сертификат вручную
certbot --nginx -d ваш-домен
```

## Поддержка

- **GitHub:** https://github.com/YOUR_USERNAME/xray-panel
- **Issues:** https://github.com/YOUR_USERNAME/xray-panel/issues
- **Wiki:** https://github.com/YOUR_USERNAME/xray-panel/wiki
- **Discussions:** https://github.com/YOUR_USERNAME/xray-panel/discussions

## Лицензия

MIT License - см. LICENSE файл

## Благодарности

- [Xray-core](https://github.com/XTLS/Xray-core)
- [sing-box](https://github.com/SagerNet/sing-box)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryproject.org/)
