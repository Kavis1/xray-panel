# Xray Panel - Установка Панели Управления

## Что устанавливается

- **Xray-core** - основной прокси-сервер (VLESS, VMess, Trojan, Shadowsocks)
- **sing-box** - для протокола Hysteria/Hysteria2
- **Redis** - брокер сообщений для Celery
- **PostgreSQL/SQLite** - база данных
- **Nginx** - веб-сервер с SSL
- **Celery Worker** - сбор трафика и статистики
- **Celery Beat** - планировщик задач (автоматический сбор каждые 5 минут)
- **FastAPI Backend** - REST API панели

## Требования

- **ОС:** Ubuntu 20.04+, Debian 11+, CentOS 8+
- **RAM:** Минимум 1GB (рекомендуется 2GB+)
- **Диск:** Минимум 10GB свободного места
- **Процессор:** 1 CPU (рекомендуется 2+)
- **Домен:** Настроенный домен с A-записью на IP сервера
- **Порты:** 80, 443 должны быть открыты

## Быстрая установка

### 1. Скачайте скрипт установки

```bash
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh
chmod +x install.sh
```

### 2. Запустите установку

```bash
sudo ./install.sh
```

### 3. Следуйте инструкциям

Скрипт запросит:
- **Домен для панели** (например: panel.example.com)
- **Email для Let's Encrypt** (для SSL сертификата)
- **Тип базы данных** (SQLite или PostgreSQL)

Всё остальное настроится автоматически!

## Что делает скрипт

1. ✅ Устанавливает все зависимости
2. ✅ Устанавливает Xray и sing-box
3. ✅ Загружает файлы панели из GitHub
4. ✅ Настраивает Python окружение
5. ✅ Создаёт и мигрирует базу данных
6. ✅ Генерирует секретные ключи
7. ✅ Создаёт systemd сервисы с автозапуском
8. ✅ Настраивает Nginx с SSL
9. ✅ Получает SSL сертификат от Let's Encrypt
10. ✅ Запускает все сервисы

## Созданные systemd сервисы

| Сервис | Описание | Порт |
|--------|----------|------|
| `xray-panel-api.service` | REST API панели | 8000 |
| `xray-panel.service` | Xray прокси-сервер | 10085 (Stats API) |
| `singbox-panel.service` | sing-box для Hysteria | 9090 (Clash API) |
| `celery-worker.service` | Сбор трафика и статистики | - |
| `celery-beat.service` | Планировщик задач (каждые 5 мин) | - |

## Управление сервисами

```bash
# Проверка статуса
systemctl status xray-panel-api
systemctl status celery-worker
systemctl status celery-beat

# Перезапуск
systemctl restart xray-panel-api
systemctl restart celery-worker

# Просмотр логов
journalctl -u xray-panel-api -f
journalctl -u celery-worker -f
```

## Первый вход

После установки:

1. Откройте `https://ваш-домен` в браузере
2. Войдите с учётными данными:
   - **Логин:** `admin`
   - **Пароль:** `admin123`
3. **ОБЯЗАТЕЛЬНО смените пароль!**

## API Key для нод

API Key будет показан в конце установки и сохранён в файл:
```bash
cat /root/xray-panel-info.txt
```

Используйте этот ключ при добавлении нод в панель.

## Файлы и директории

```
/opt/xray-panel/                    # Главная директория
├── backend/                        # Backend API
│   ├── venv/                       # Python окружение
│   ├── app/                        # Код приложения
│   ├── .env                        # Конфигурация
│   └── panel.db                    # База данных (SQLite)
├── xray_config.json                # Конфиг Xray
└── singbox_config.json             # Конфиг sing-box

/etc/systemd/system/                # Systemd сервисы
├── xray-panel-api.service
├── xray-panel.service
├── singbox-panel.service
├── celery-worker.service
└── celery-beat.service

/etc/nginx/sites-available/
└── xray-panel                      # Nginx конфиг
```

## Обновление

```bash
cd /opt/xray-panel
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart xray-panel-api celery-worker celery-beat
```

## Резервное копирование

### База данных SQLite
```bash
cp /opt/xray-panel/backend/panel.db /root/backup-$(date +%Y%m%d).db
```

### База данных PostgreSQL
```bash
sudo -u postgres pg_dump xray_panel > /root/backup-$(date +%Y%m%d).sql
```

### Конфигурация
```bash
tar -czf /root/panel-backup-$(date +%Y%m%d).tar.gz /opt/xray-panel/backend/.env
```

## Решение проблем

### Панель не отвечает
```bash
systemctl status xray-panel-api
journalctl -u xray-panel-api -n 50
```

### Трафик не собирается
```bash
# Проверьте Celery Worker и Beat
systemctl status celery-worker
systemctl status celery-beat

# Проверьте логи
journalctl -u celery-worker -f

# Проверьте Redis
systemctl status redis-server
redis-cli ping
```

### SSL сертификат не получен
```bash
# Убедитесь что DNS настроен правильно
dig +short ваш-домен

# Попробуйте получить сертификат вручную
certbot --nginx -d ваш-домен
```

### Xray не запускается
```bash
# Проверьте конфиг
xray -test -c /opt/xray-panel/xray_config.json

# Проверьте логи
journalctl -u xray-panel -n 50
```

## Архитектура сбора трафика

```
┌─────────────────┐
│   Пользователь  │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼──┐  ┌───▼────┐
│ Xray │  │sing-box│
└───┬──┘  └───┬────┘
    │         │
    │ Stats   │ Clash
    │ API     │ API
    │ :10085  │ :9090
    │         │
┌───▼─────────▼───┐
│ Celery Worker   │  ← Собирает трафик каждые 5 мин
└────────┬────────┘
         │
    ┌────▼────┐
    │   БД    │  ← Сохраняет статистику
    └─────────┘
```

## Поддержка

- GitHub Issues: https://github.com/YOUR_USERNAME/xray-panel/issues
- Документация: https://github.com/YOUR_USERNAME/xray-panel/wiki
