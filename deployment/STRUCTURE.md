# Структура файлов для GitHub

Это файл с инструкциями какие файлы нужно загрузить в GitHub.

## Структура репозитория

```
xray-panel/
├── deployment/
│   ├── README.md                    # ✅ Создан
│   ├── STRUCTURE.md                 # ✅ Этот файл
│   ├── panel/
│   │   ├── install.sh               # ✅ Создан
│   │   └── README.md                # ✅ Создан
│   └── node/
│       ├── install-node.sh          # ✅ Создан
│       └── README.md                # ✅ Создан
│
├── backend/                         # Файлы панели
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── node.py
│   │   │   ├── inbound.py
│   │   │   ├── admin.py
│   │   │   ├── webhook.py
│   │   │   ├── stats.py
│   │   │   ├── settings.py
│   │   │   └── audit.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── node.py
│   │   │   ├── inbound.py
│   │   │   ├── admin.py
│   │   │   └── auth.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py
│   │   │           ├── users.py
│   │   │           ├── users_extensions.py
│   │   │           ├── nodes.py
│   │   │           ├── inbounds.py
│   │   │           ├── admins.py
│   │   │           ├── subscriptions.py
│   │   │           ├── templates.py
│   │   │           └── webhooks.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── xray/
│   │   │   │   ├── __init__.py
│   │   │   │   └── config_builder.py
│   │   │   ├── singbox/
│   │   │   │   ├── __init__.py
│   │   │   │   └── config_builder.py
│   │   │   ├── inbound/
│   │   │   │   ├── __init__.py
│   │   │   │   └── templates.py        # ⚠️ ВАЖНО: с безопасными шаблонами
│   │   │   ├── node/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── grpc_client.py
│   │   │   │   └── sync.py
│   │   │   ├── subscription/
│   │   │   │   ├── __init__.py
│   │   │   │   └── generator.py
│   │   │   ├── telegram/
│   │   │   │   ├── __init__.py
│   │   │   │   └── bot.py
│   │   │   └── webhook/
│   │   │       ├── __init__.py
│   │   │       └── sender.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py              # ⚠️ ВАЖНО: с исправленным сбором трафика
│   │   ├── grpc_gen/
│   │   │   ├── __init__.py
│   │   │   ├── node_pb2.py
│   │   │   └── node_pb2_grpc.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   ├── cli/
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   └── utils/
│   │       └── __init__.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 692281e7034b_initial_migration.py
│   │       └── 493d3e718f32_add_block_torrents_to_inbound_and_max_.py
│   ├── tests/
│   │   └── __init__.py
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt              # ⚠️ ВАЖНО: с requests
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── README.md
│
├── node/                            # Файлы ноды
│   ├── cmd/
│   │   └── main.go
│   ├── pkg/
│   │   ├── api/
│   │   │   └── grpc_server.go
│   │   ├── stats/
│   │   │   └── collector.go
│   │   ├── types/
│   │   │   └── types.go
│   │   └── xray/
│   │       └── manager.go
│   ├── proto/
│   │   ├── node.pb.go
│   │   └── node_grpc.pb.go
│   ├── config/
│   │   └── config.go
│   ├── .env.example
│   ├── go.mod
│   ├── go.sum
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                        # (Опционально) Web UI
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── docs/                            # Документация
│   ├── installation.md
│   ├── configuration.md
│   ├── api.md
│   └── troubleshooting.md
│
├── scripts/                         # Дополнительные скрипты
│   └── restart-all.sh
│
├── .gitignore
├── LICENSE
└── README.md                        # Главный README
```

## Что нужно сделать перед загрузкой в GitHub

### 1. Скопировать файлы панели
```bash
cd /root/panel
# Убедитесь что backend/ содержит все необходимые файлы
```

### 2. Скопировать файлы ноды
```bash
cd /root/panel
# Убедитесь что node/ содержит все необходимые файлы
```

### 3. Проверить важные файлы

#### ⚠️ backend/requirements.txt
Должен содержать:
```
requests==2.31.0  # ← ВАЖНО для sing-box Clash API
```

#### ⚠️ backend/app/workers/tasks.py
Должен содержать:
- `collect_user_traffic_stats_async()` с поддержкой Xray CLI + sing-box Clash API
- `collect_node_stats_async()` с суммированием трафика всех юзеров
- Использование `uploadTotal` и `downloadTotal` из sing-box

#### ⚠️ backend/app/services/inbound/templates.py
Должен содержать только безопасные шаблоны (с TLS):
- VLESS Reality
- VLESS WebSocket TLS
- VMess gRPC TLS
- Trojan TLS
- Shadowsocks
- Hysteria2
- VLESS Reality HTTP/2

НЕ должен содержать:
- ❌ VLESS без TLS
- ❌ VMess WebSocket без TLS

### 4. Создать .gitignore
```bash
cat > /root/panel/.gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/
*.egg-info/
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3

# Env files
.env
*.env
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/
celerybeat-schedule

# OS
.DS_Store
Thumbs.db

# Node
node_modules/
npm-debug.log

# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
vendor/

# Temp
tmp/
temp/
*.tmp
EOF
```

### 5. Обновить URL в скриптах
В файлах `install.sh` и `install-node.sh` замените:
```bash
# Было:
REPO_URL="https://github.com/YOUR_USERNAME/xray-panel"

# На ваш репозиторий:
REPO_URL="https://github.com/ваш-username/xray-panel"
```

### 6. Создать LICENSE
```bash
cat > /root/panel/LICENSE << 'EOF'
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[... полный текст MIT лицензии]
EOF
```

### 7. Создать главный README.md
```bash
# Скопируйте deployment/README.md в корень как основу
cp /root/panel/deployment/README.md /root/panel/README.md
```

## Команды для загрузки в GitHub

```bash
cd /root/panel

# Инициализация git (если еще не сделано)
git init

# Добавить все файлы
git add .

# Первый коммит
git commit -m "Initial commit: Xray Panel with auto-deployment scripts

- Panel installation script with Celery, Redis, Xray, sing-box
- Node installation script with gRPC service
- Traffic collection from Xray (CLI) and sing-box (Clash API)
- Systemd services with auto-restart
- SSL support with Let's Encrypt
- Complete documentation"

# Добавить remote (замените на ваш репозиторий)
git remote add origin https://github.com/YOUR_USERNAME/xray-panel.git

# Отправить в GitHub
git branch -M main
git push -u origin main
```

## После загрузки в GitHub

### 1. Проверьте что файлы доступны
```bash
# Попробуйте скачать скрипт
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh
```

### 2. Обновите README.md на GitHub
Отредактируйте через web интерфейс и добавьте:
- Скриншоты (если есть)
- Бейдж со статусом
- Ссылки на demo (если есть)

### 3. Создайте Releases
В GitHub создайте первый релиз v1.0.0 с описанием возможностей.

### 4. Настройте GitHub Pages (опционально)
Для документации можно использовать GitHub Pages.

## Проверка работы скриптов

### Тест установки панели
```bash
# На чистом Ubuntu сервере:
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh
chmod +x install.sh
sudo ./install.sh
```

### Тест установки ноды
```bash
# На чистом Ubuntu сервере:
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/node/install-node.sh
chmod +x install-node.sh
sudo ./install-node.sh
```

## Файлы которые НЕ нужно загружать

❌ Не загружайте:
- `.env` файлы с секретами
- `panel.db` базу данных
- `venv/` виртуальное окружение Python
- `node_modules/` если есть frontend
- `__pycache__/` скомпилированные файлы Python
- Скомпилированный бинарный файл ноды `node/node`
- `celerybeat-schedule` файл планировщика
- Любые логи `*.log`

✅ Загружайте:
- Все `.py` файлы
- Все `.go` файлы
- `requirements.txt`, `go.mod`, `go.sum`
- `.env.example` (без секретов)
- Все `.sh` скрипты
- Все `.md` документацию
- `.gitignore`
- `LICENSE`

## Поддержка

После загрузки в GitHub, пользователи смогут:
1. Клонировать репозиторий
2. Скачать install.sh напрямую
3. Создавать Issues для багов
4. Предлагать Pull Requests
5. Форкать проект

Убедитесь что в README есть раздел "Contributing" с инструкциями как предлагать изменения.
