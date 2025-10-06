# Xray Panel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://golang.org/dl/)

Современная панель управления для Xray VPN с автоматической установкой и поддержкой множественных нод.

## 🚀 Быстрый старт

### Установка панели (5-10 минут)

```bash
wget https://raw.githubusercontent.com/Kavis1/xray-panel/main/deployment/panel/install.sh
chmod +x install.sh
sudo ./install.sh
```

Скрипт запросит:
- Домен для панели (например: `panel.example.com`)
- Email для Let's Encrypt SSL сертификата
- Тип базы данных (SQLite или PostgreSQL)

Всё остальное настроится автоматически!

### Установка ноды (3-5 минут)

```bash
wget https://raw.githubusercontent.com/Kavis1/xray-panel/main/deployment/node/install-node.sh
chmod +x install-node.sh
sudo ./install-node.sh
```

После установки скопируйте данные подключения и добавьте ноду в панель через Web UI.

## ✨ Возможности

- 🔐 **Безопасность**: Только TLS конфигурации, автоматический SSL (Let's Encrypt)
- 📊 **Автоматический сбор статистики**: Трафик каждого пользователя обновляется каждые 5 минут
- 🌍 **Multi-node**: Поддержка неограниченного количества нод в разных локациях
- 🔄 **Автоматическая синхронизация**: Конфигурации применяются мгновенно
- 📡 **Множественные протоколы**: VLESS, VMess, Trojan, Shadowsocks, Hysteria2
- 🛠️ **Systemd сервисы**: Автозапуск и автоперезапуск всех компонентов
- 🎯 **REST API**: Полноценный API с автоматической документацией (Swagger)

## 🏗️ Архитектура

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

## 📦 Что устанавливается

### Панель
- **FastAPI** - REST API сервер
- **Xray-core** - прокси-сервер (VLESS, VMess, Trojan, Shadowsocks)
- **sing-box** - для протокола Hysteria2
- **Redis** - брокер сообщений
- **PostgreSQL/SQLite** - база данных
- **Nginx** - веб-сервер с SSL
- **Celery Worker** - сбор трафика
- **Celery Beat** - планировщик задач

### Нода
- **Xray-core** - прокси-сервер
- **sing-box** - для Hysteria2
- **Node Service** - gRPC API для связи с панелью
- **Go** - для сборки Node Service

Все компоненты настраиваются как systemd сервисы с автозапуском.

## 🔧 Системные требования

### Панель
- **ОС**: Ubuntu 20.04+, Debian 11+, CentOS 8+
- **RAM**: 1GB+ (рекомендуется 2GB)
- **CPU**: 1 core (рекомендуется 2)
- **Диск**: 10GB+
- **Домен**: С A-записью на IP сервера
- **Порты**: 80, 443 (открыты)

### Нода
- **ОС**: Ubuntu 20.04+, Debian 11+, CentOS 8+
- **RAM**: 512MB+ (рекомендуется 1GB)
- **CPU**: 1 core
- **Диск**: 5GB+
- **Порты**: 50051 (gRPC), 443, 80 (открыты)

## 📚 Документация

- [Установка панели](./deployment/panel/README.md)
- [Установка ноды](./deployment/node/README.md)
- [Общая документация](./deployment/README.md)
- [Структура проекта](./deployment/STRUCTURE.md)
- [Чеклист для контрибьюторов](./deployment/CHECKLIST.md)

## 🎯 Поддерживаемые протоколы

| Протокол | Описание | Безопасность |
|----------|----------|--------------|
| **VLESS Reality** | Современный протокол с маскировкой TLS | ✅ TLS |
| **VLESS WebSocket** | VLESS через WebSocket | ✅ TLS |
| **VMess gRPC** | VMess через gRPC | ✅ TLS |
| **Trojan** | Trojan-GFW | ✅ TLS |
| **Shadowsocks** | Популярный протокол | ✅ Encrypted |
| **Hysteria2** | Высокоскоростной UDP протокол | ✅ TLS |

**Все протоколы используют TLS шифрование!**

## 🔄 Сбор трафика

Система автоматически собирает статистику:

**Панель (локальная нода):**
- Celery Beat запускает задачи каждые 5 минут
- Celery Worker собирает данные из Xray CLI и sing-box Clash API
- Трафик каждого пользователя обновляется в базе данных

**Удалённые ноды:**
- Node Service собирает статистику локально
- Отправляет данные на панель по gRPC
- Трафик синхронизируется автоматически

## 🛠️ Управление

### Панель

```bash
# Проверка статуса
systemctl status xray-panel-api
systemctl status celery-worker
systemctl status celery-beat

# Перезапуск
systemctl restart xray-panel-api
systemctl restart celery-worker
systemctl restart celery-beat

# Логи
journalctl -u xray-panel-api -f
journalctl -u celery-worker -f
```

### Нода

```bash
# Проверка статуса
systemctl status xray-panel-node
systemctl status xray-node
systemctl status singbox-node

# Перезапуск
systemctl restart xray-panel-node
systemctl restart xray-node
systemctl restart singbox-node

# Логи
journalctl -u xray-panel-node -f
journalctl -u xray-node -f
```

## 🔐 Безопасность

- ✅ Все протоколы используют TLS шифрование
- ✅ SSL сертификаты от Let's Encrypt
- ✅ API ключи для защиты связи с нодами
- ✅ JWT токены для админ панели
- ✅ Валидация всех конфигураций
- ✅ Аудит действий администраторов

## 📊 Первый вход

После установки панели:

1. Откройте `https://ваш-домен` в браузере
2. Войдите с учётными данными:
   - **Логин**: `admin`
   - **Пароль**: `admin123`
3. **⚠️ ОБЯЗАТЕЛЬНО смените пароль!**

API документация доступна по адресу: `https://ваш-домен/docs`

## 🔄 Обновление

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

## 🐛 Решение проблем

### Панель не отвечает
```bash
systemctl status xray-panel-api
journalctl -u xray-panel-api -n 50
```

### Трафик не собирается
```bash
systemctl status celery-worker celery-beat
journalctl -u celery-worker -f
redis-cli ping
```

### Нода не подключается
```bash
journalctl -u xray-panel-node -n 50
telnet IP_ПАНЕЛИ 50051
```

Подробнее в [документации](./deployment/README.md#решение-проблем).

## 💾 Резервное копирование

```bash
# База данных SQLite
cp /opt/xray-panel/backend/panel.db /root/backup-$(date +%Y%m%d).db

# База данных PostgreSQL
sudo -u postgres pg_dump xray_panel > /root/backup-$(date +%Y%m%d).sql

# Конфигурация
tar -czf /root/panel-backup-$(date +%Y%m%d).tar.gz \
    /opt/xray-panel/backend/.env \
    /root/xray-panel-info.txt
```

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! 

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

См. [CHECKLIST.md](./deployment/CHECKLIST.md) для деталей.

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- [Xray-core](https://github.com/XTLS/Xray-core) - основной прокси-сервер
- [sing-box](https://github.com/SagerNet/sing-box) - Hysteria протокол
- [FastAPI](https://fastapi.tiangolo.com/) - веб-фреймворк
- [Celery](https://docs.celeryproject.org/) - фоновые задачи

## 📧 Поддержка

- **Issues**: [GitHub Issues](https://github.com/Kavis1/xray-panel/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kavis1/xray-panel/discussions)

## ⭐ Star History

Если проект полезен, поставьте звезду! ⭐

---

**Сделано с ❤️ для сообщества**
