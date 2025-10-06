# Xray Panel - Установка Ноды

## Что устанавливается

- **Xray-core** - прокси-сервер (VLESS, VMess, Trojan, Shadowsocks)
- **sing-box** - для протокола Hysteria/Hysteria2
- **Go** - для сборки Node Service
- **Node Service** - gRPC сервер для связи с панелью
- **Systemd сервисы** - автозапуск и мониторинг

## Требования

- **ОС:** Ubuntu 20.04+, Debian 11+, CentOS 8+
- **RAM:** Минимум 512MB (рекомендуется 1GB+)
- **Диск:** Минимум 5GB свободного места
- **Процессор:** 1 CPU
- **Порты:** 50051 (gRPC), 443, 80 должны быть открыты

## Быстрая установка

### 1. Скачайте скрипт установки

```bash
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/node/install-node.sh
chmod +x install-node.sh
```

### 2. Запустите установку

```bash
sudo ./install-node.sh
```

### 3. Следуйте инструкциям

Скрипт запросит:
- **Название ноды** (например: DE-Node-1)

IP адрес определяется автоматически, API ключ генерируется автоматически.

### 4. Сохраните данные подключения

В конце установки скрипт выведет:
```
╔════════════════════════════════════════╗
║  ДАННЫЕ ДЛЯ ПОДКЛЮЧЕНИЯ К ПАНЕЛИ       ║
╠════════════════════════════════════════╣
║  Название:  DE-Node-1                  ║
║  IP адрес:  123.45.67.89               ║
║  API Port:  50051                      ║
║  Protocol:  grpc                       ║
║  API Key:   abcd1234...                ║
╚════════════════════════════════════════╝
```

**СОХРАНИТЕ ЭТИ ДАННЫЕ!** Они также сохранены в `/root/xray-node-info.txt`

## Что делает скрипт

1. ✅ Определяет внешний IP автоматически
2. ✅ Устанавливает все зависимости
3. ✅ Устанавливает Xray и sing-box
4. ✅ Устанавливает Go и собирает Node Service
5. ✅ Генерирует API ключ
6. ✅ Создаёт systemd сервисы с автозапуском
7. ✅ Настраивает firewall
8. ✅ Запускает все сервисы

## Созданные systemd сервисы

| Сервис | Описание | Порт |
|--------|----------|------|
| `xray-node.service` | Xray прокси-сервер | 10085 (Stats API) |
| `singbox-node.service` | sing-box для Hysteria | 9090 (Clash API) |
| `xray-panel-node.service` | Node Service (gRPC) | 50051 |

## Управление сервисами

```bash
# Проверка статуса всех сервисов
systemctl status xray-node
systemctl status singbox-node
systemctl status xray-panel-node

# Перезапуск
systemctl restart xray-node
systemctl restart singbox-node
systemctl restart xray-panel-node

# Просмотр логов
journalctl -u xray-node -f
journalctl -u singbox-node -f
journalctl -u xray-panel-node -f
```

## Добавление ноды в панель

### 1. Войдите в панель управления

Откройте панель в браузере и войдите как администратор.

### 2. Перейдите в раздел Nodes

Меню → Nodes → Add Node

### 3. Заполните форму

Используйте данные из вывода скрипта:
- **Name:** DE-Node-1
- **Address:** 123.45.67.89
- **API Port:** 50051
- **API Protocol:** grpc
- **API Key:** (вставьте сгенерированный ключ)
- **Enabled:** ✅ (включено)

### 4. Нажмите "Connect"

Панель подключится к ноде и начнёт получать статистику.

## Файлы и директории

```
/opt/xray-panel-node/               # Главная директория
├── xray-panel-node                 # Исполняемый файл Node Service
├── .env                            # Конфигурация ноды
├── xray_config.json                # Конфиг Xray (управляется панелью)
└── singbox_config.json             # Конфиг sing-box (управляется панелью)

/etc/systemd/system/                # Systemd сервисы
├── xray-node.service
├── singbox-node.service
└── xray-panel-node.service

/root/xray-node-info.txt            # Данные подключения (бэкап)
```

## Как работает нода

```
┌──────────────┐
│    Панель    │
└──────┬───────┘
       │ gRPC :50051
       │
┌──────▼───────────────────┐
│  Node Service (gRPC API) │
└──────┬──────────┬────────┘
       │          │
   ┌───▼──┐  ┌───▼────┐
   │ Xray │  │sing-box│
   └───┬──┘  └───┬────┘
       │         │
   ┌───▼─────────▼────┐
   │   Пользователи   │
   └──────────────────┘
```

**Процесс:**
1. Панель подключается к ноде по gRPC (порт 50051)
2. Панель отправляет конфигурации (пользователи, inbound'ы)
3. Node Service применяет конфиги к Xray и sing-box
4. Node Service собирает статистику трафика
5. Node Service отправляет статистику на панель
6. Всё обновляется автоматически каждые 5 минут

## Проверка работы

### Проверка подключения к панели
```bash
# Посмотрите логи Node Service
journalctl -u xray-panel-node -n 50

# Должны быть сообщения о подключении к панели
```

### Проверка Xray
```bash
# Проверка статуса
systemctl status xray-node

# Проверка Stats API
xray api statsquery --server=127.0.0.1:10085 -pattern="user>>>"
```

### Проверка sing-box
```bash
# Проверка статуса
systemctl status singbox-node

# Проверка Clash API
curl -s http://127.0.0.1:9090/connections | jq
```

### Проверка сети
```bash
# Проверьте что порт 50051 открыт
netstat -tlnp | grep 50051

# Проверьте firewall
ufw status
```

## Обновление ноды

```bash
cd /opt/xray-panel-node
git pull
/usr/local/go/bin/go build -o xray-panel-node cmd/main.go
systemctl restart xray-panel-node
```

## Удаление ноды

### 1. Отключите в панели
Сначала отключите или удалите ноду в панели управления.

### 2. Остановите сервисы
```bash
systemctl stop xray-panel-node singbox-node xray-node
systemctl disable xray-panel-node singbox-node xray-node
```

### 3. Удалите файлы
```bash
rm -rf /opt/xray-panel-node
rm /etc/systemd/system/xray-node.service
rm /etc/systemd/system/singbox-node.service
rm /etc/systemd/system/xray-panel-node.service
systemctl daemon-reload
```

## Решение проблем

### Нода не подключается к панели
```bash
# Проверьте логи
journalctl -u xray-panel-node -n 100

# Проверьте сеть
ping IP_ПАНЕЛИ
telnet IP_ПАНЕЛИ 50051

# Проверьте API ключ в .env
cat /opt/xray-panel-node/.env
```

### Трафик не передаётся
```bash
# Проверьте Xray Stats API
xray api statsquery --server=127.0.0.1:10085 -pattern="user>>>"

# Проверьте sing-box Clash API
curl http://127.0.0.1:9090/connections

# Проверьте что Node Service работает
systemctl status xray-panel-node
```

### Xray не запускается
```bash
# Проверьте конфиг
xray -test -c /opt/xray-panel-node/xray_config.json

# Проверьте логи
journalctl -u xray-node -n 50
```

### sing-box не запускается
```bash
# Проверьте конфиг
sing-box check -c /opt/xray-panel-node/singbox_config.json

# Проверьте логи
journalctl -u singbox-node -n 50
```

## Безопасность

### Firewall
Скрипт автоматически открывает необходимые порты. Рекомендуется ограничить доступ:

```bash
# Разрешить gRPC только с IP панели
ufw allow from IP_ПАНЕЛИ to any port 50051
```

### API Key
Храните API ключ в секрете. Если ключ скомпрометирован:

1. Сгенерируйте новый ключ: `openssl rand -hex 32`
2. Обновите в `/opt/xray-panel-node/.env`
3. Обновите в панели (Settings → Nodes → Edit)
4. Перезапустите: `systemctl restart xray-panel-node`

## Мониторинг

### Использование ресурсов
```bash
# CPU и память
top -p $(pgrep -d, -f "xray|sing-box|xray-panel-node")

# Трафик
vnstat -i eth0
```

### Количество подключений
```bash
# Xray
xray api statsquery --server=127.0.0.1:10085 -pattern="user>>>"

# sing-box
curl -s http://127.0.0.1:9090/connections | jq '.connections | length'
```

## Поддержка

- GitHub Issues: https://github.com/YOUR_USERNAME/xray-panel/issues
- Документация: https://github.com/YOUR_USERNAME/xray-panel/wiki
