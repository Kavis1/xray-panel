#!/bin/bash

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Проверка режима работы
UPDATE_MODE=false
if [ -d "/root/panel" ] && [ -f "/root/panel/backend/panel.db" ]; then
    UPDATE_MODE=true
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}  Обнаружена установленная панель${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    echo ""
    echo -e "${BLUE}Режим: ОБНОВЛЕНИЕ${NC}"
    echo ""
else
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}  Xray Panel - Установка Панели${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo -e "${BLUE}Режим: НОВАЯ УСТАНОВКА${NC}"
    echo ""
fi

# Проверка root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен быть запущен с правами root${NC}" 
   exit 1
fi

# Определение ОС
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Не удалось определить ОС${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Определена ОС: $OS"

# РЕЖИМ ОБНОВЛЕНИЯ
if [ "$UPDATE_MODE" = true ]; then
    echo ""
    echo -e "${YELLOW}=== Обновление панели ===${NC}"
    echo ""
    
    INSTALL_DIR="/root/panel"
    REPO_URL="https://github.com/Kavis1/xray-panel.git"
    
    echo -e "${BLUE}[1/4]${NC} Загрузка обновлений..."
    cd /tmp
    rm -rf temp_panel_update
    git clone -q "$REPO_URL" temp_panel_update || {
        echo -e "${RED}Ошибка загрузки обновлений${NC}"
        exit 1
    }
    
    echo -e "${BLUE}[2/4]${NC} Создание резервных копий..."
    cp $INSTALL_DIR/backend/.env /tmp/.env.backup
    cp $INSTALL_DIR/backend/panel.db /tmp/panel.db.backup
    
    echo -e "${BLUE}[3/4]${NC} Обновление файлов..."
    # Обновляем только backend и workers
    cd $INSTALL_DIR/backend
    cp -r /tmp/temp_panel_update/backend/app .
    cp /tmp/temp_panel_update/backend/requirements.txt .
    
    # Устанавливаем новые зависимости если есть
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    # Применяем миграции
    alembic upgrade head
    
    # Восстанавливаем конфиги
    cp /tmp/.env.backup .env
    
    echo -e "${BLUE}[4/4]${NC} Перезапуск сервисов..."
    # Перезапускаем сервисы
    pkill -f uvicorn || true
    pkill -f celery || true
    
    sleep 2
    
    # Запускаем заново
    cd $INSTALL_DIR/backend
    nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/panel.log 2>&1 &
    nohup venv/bin/celery -A app.workers.celery_app worker --loglevel=info > /tmp/celery_worker.log 2>&1 &
    nohup venv/bin/celery -A app.workers.celery_app beat --loglevel=info > /tmp/celery_beat.log 2>&1 &
    
    # Очистка
    rm -rf /tmp/temp_panel_update /tmp/*.backup
    
    sleep 3
    
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✓✓✓ Обновление завершено! ✓✓✓${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo "Проверка сервисов:"
    curl -s http://localhost:8000/health && echo " ✓ Panel API работает" || echo " ✗ Panel API не отвечает"
    ps aux | grep -E "(uvicorn|celery)" | grep -v grep | head -3
    echo ""
    echo -e "${GREEN}Панель обновлена и перезапущена!${NC}"
    echo -e "URL: https://$(cat $INSTALL_DIR/backend/.env | grep DOMAIN | cut -d'=' -f2)"
    
    exit 0
fi

# Запрос данных от пользователя
echo ""
echo -e "${YELLOW}=== Настройка параметров ===${NC}"
echo ""

# Домен для SSL
read -p "Введите домен для панели (например: panel.example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Домен обязателен!${NC}"
    exit 1
fi

# Email для Let's Encrypt
read -p "Введите email для Let's Encrypt: " SSL_EMAIL
if [ -z "$SSL_EMAIL" ]; then
    echo -e "${RED}Email обязателен!${NC}"
    exit 1
fi

# База данных
echo ""
echo -e "${YELLOW}Выберите базу данных:${NC}"
echo "1) SQLite (рекомендуется для начала)"
echo "2) PostgreSQL (для production)"
read -p "Выбор [1/2]: " DB_CHOICE

if [ "$DB_CHOICE" == "2" ]; then
    USE_POSTGRES=true
    read -p "PostgreSQL пароль [оставьте пустым для генерации]: " DB_PASSWORD
    if [ -z "$DB_PASSWORD" ]; then
        DB_PASSWORD=$(openssl rand -base64 32)
    fi
else
    USE_POSTGRES=false
fi

# Генерация секретов
SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 32)

echo ""
echo -e "${GREEN}✓${NC} Параметры настроены"
echo ""

# Установка зависимостей
echo -e "${YELLOW}[1/8]${NC} Установка системных зависимостей..."

if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get update -qq
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        redis-server \
        nginx \
        certbot \
        python3-certbot-nginx \
        curl \
        wget \
        unzip \
        jq \
        sqlite3 > /dev/null 2>&1
    
    if [ "$USE_POSTGRES" = true ]; then
        apt-get install -y -qq postgresql postgresql-contrib > /dev/null 2>&1
    fi
    
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]]; then
    yum install -y python3 python3-pip redis nginx certbot curl wget unzip jq sqlite > /dev/null 2>&1
    
    if [ "$USE_POSTGRES" = true ]; then
        yum install -y postgresql-server postgresql-contrib > /dev/null 2>&1
    fi
else
    echo -e "${RED}Неподдерживаемая ОС: $OS${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Системные зависимости установлены"

# Установка Xray
echo -e "${YELLOW}[2/8]${NC} Установка Xray-core..."
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install -u root > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Xray-core установлен"

# Установка sing-box
echo -e "${YELLOW}[3/8]${NC} Установка sing-box..."
SINGBOX_VERSION="1.12.9"
wget -q "https://github.com/SagerNet/sing-box/releases/download/v${SINGBOX_VERSION}/sing-box-${SINGBOX_VERSION}-linux-amd64.tar.gz"
tar -xzf "sing-box-${SINGBOX_VERSION}-linux-amd64.tar.gz"
cp "sing-box-${SINGBOX_VERSION}-linux-amd64/sing-box" /usr/bin/
chmod +x /usr/bin/sing-box
rm -rf "sing-box-${SINGBOX_VERSION}-linux-amd64"*
echo -e "${GREEN}✓${NC} sing-box установлен"

# Создание директорий
INSTALL_DIR="/opt/xray-panel"
echo -e "${YELLOW}[4/8]${NC} Создание директорий..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Загрузка файлов панели из GitHub
echo -e "${YELLOW}[5/8]${NC} Загрузка файлов панели..."
# TODO: Заменить на ваш GitHub репозиторий
REPO_URL="https://github.com/Kavis1/xray-panel"
git clone "$REPO_URL" . || {
    echo -e "${RED}Ошибка загрузки файлов. Убедитесь что репозиторий доступен.${NC}"
    exit 1
}
echo -e "${GREEN}✓${NC} Файлы панели загружены"

# Настройка Python окружения
echo -e "${YELLOW}[6/8]${NC} Настройка Python окружения..."
cd $INSTALL_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓${NC} Python окружение настроено"

# Настройка базы данных
echo -e "${YELLOW}[7/8]${NC} Настройка базы данных..."

if [ "$USE_POSTGRES" = true ]; then
    systemctl enable --now postgresql > /dev/null 2>&1
    sudo -u postgres psql -c "CREATE USER xray_panel WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE xray_panel OWNER xray_panel;" 2>/dev/null || true
    
    DATABASE_URL="postgresql://xray_panel:$DB_PASSWORD@localhost/xray_panel"
else
    DATABASE_URL="sqlite:///panel.db"
fi

# Создание .env файла
cat > .env << EOF
# Database
DATABASE_URL=$DATABASE_URL

# Security
SECRET_KEY=$SECRET_KEY
API_KEY=$API_KEY

# Server
DEBUG=false
ALLOWED_HOSTS=*

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Panel Settings
PANEL_DOMAIN=$DOMAIN
PANEL_SSL_EMAIL=$SSL_EMAIL
EOF

# Запуск миграций
alembic upgrade head
echo -e "${GREEN}✓${NC} База данных настроена"

# Создание systemd сервисов
echo -e "${YELLOW}[8/8]${NC} Создание systemd сервисов..."

# 1. Xray Panel API
cat > /etc/systemd/system/xray-panel-api.service << 'APIEOF'
[Unit]
Description=Xray Panel API Server
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xray-panel/backend
Environment="PATH=/opt/xray-panel/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/xray-panel/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
APIEOF

# 2. Xray для панели
cat > /etc/systemd/system/xray-panel.service << 'XRAYEOF'
[Unit]
Description=Xray Panel Proxy Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/xray run -c /opt/xray-panel/xray_config.json
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
XRAYEOF

# 3. sing-box для Hysteria
cat > /etc/systemd/system/singbox-panel.service << 'SINGEOF'
[Unit]
Description=sing-box Panel Service (Hysteria)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/sing-box run -c /opt/xray-panel/singbox_config.json
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SINGEOF

# 4. Celery Worker
cat > /etc/systemd/system/celery-worker.service << 'WORKEOF'
[Unit]
Description=Celery Worker for Xray Panel
After=network.target redis.service xray-panel.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xray-panel/backend
Environment="PATH=/opt/xray-panel/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/xray-panel/backend/venv/bin/celery -A app.workers.celery_app worker --loglevel=info
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
WORKEOF

# 5. Celery Beat (Scheduler)
cat > /etc/systemd/system/celery-beat.service << 'BEATEOF'
[Unit]
Description=Celery Beat Scheduler for Xray Panel
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xray-panel/backend
Environment="PATH=/opt/xray-panel/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/xray-panel/backend/venv/bin/celery -A app.workers.celery_app beat --loglevel=info
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
BEATEOF

# Создание начальных конфигов
mkdir -p /opt/xray-panel

# Базовый Xray конфиг с Stats API
cat > /opt/xray-panel/xray_config.json << 'XRAYJSON'
{
  "log": {
    "loglevel": "warning"
  },
  "api": {
    "tag": "api",
    "services": [
      "StatsService"
    ]
  },
  "stats": {},
  "policy": {
    "levels": {
      "0": {
        "statsUserUplink": true,
        "statsUserDownlink": true
      }
    },
    "system": {
      "statsInboundUplink": true,
      "statsInboundDownlink": true
    }
  },
  "inbounds": [
    {
      "tag": "api",
      "listen": "127.0.0.1",
      "port": 10085,
      "protocol": "dokodemo-door",
      "settings": {
        "address": "127.0.0.1"
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    }
  ],
  "routing": {
    "rules": [
      {
        "type": "field",
        "inboundTag": ["api"],
        "outboundTag": "api"
      }
    ]
  }
}
XRAYJSON

# Базовый sing-box конфиг с Clash API
cat > /opt/xray-panel/singbox_config.json << 'SINGJSON'
{
  "log": {
    "level": "warn",
    "timestamp": true
  },
  "inbounds": [],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ],
  "experimental": {
    "clash_api": {
      "external_controller": "127.0.0.1:9090",
      "external_ui": "",
      "secret": ""
    }
  }
}
SINGJSON

# Настройка Nginx
cat > /etc/nginx/sites-available/xray-panel << 'NGINXEOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    # SSL будет настроен certbot
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINXEOF

sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/xray-panel
ln -sf /etc/nginx/sites-available/xray-panel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Reload systemd
systemctl daemon-reload

# Запуск сервисов
systemctl enable redis-server > /dev/null 2>&1
systemctl start redis-server

systemctl enable xray-panel.service
systemctl start xray-panel.service

systemctl enable singbox-panel.service
systemctl start singbox-panel.service

systemctl enable celery-worker.service
systemctl start celery-worker.service

systemctl enable celery-beat.service
systemctl start celery-beat.service

systemctl enable xray-panel-api.service
systemctl start xray-panel-api.service

echo -e "${GREEN}✓${NC} Сервисы запущены"

# Получение SSL сертификата
echo ""
echo -e "${YELLOW}Получение SSL сертификата...${NC}"
systemctl reload nginx
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$SSL_EMAIL" --redirect > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠${NC} Не удалось получить SSL. Проверьте DNS записи для $DOMAIN"
    echo -e "${YELLOW}⚠${NC} Вы можете запустить позже: certbot --nginx -d $DOMAIN"
}

# Проверка статуса
sleep 3
echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✓✓✓ Установка завершена успешно! ✓✓✓${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "${YELLOW}Информация для доступа:${NC}"
echo ""
echo -e "  ${GREEN}URL:${NC} https://$DOMAIN"
echo -e "  ${GREEN}Логин:${NC} admin"
echo -e "  ${GREEN}Пароль:${NC} admin123 ${RED}(ОБЯЗАТЕЛЬНО СМЕНИТЕ!)${NC}"
echo ""
echo -e "${YELLOW}API Key для нод:${NC}"
echo -e "  ${GREEN}$API_KEY${NC}"
echo ""
echo -e "${YELLOW}Управление сервисами:${NC}"
echo -e "  systemctl status xray-panel-api     ${BLUE}# API панели${NC}"
echo -e "  systemctl status xray-panel         ${BLUE}# Xray прокси${NC}"
echo -e "  systemctl status singbox-panel      ${BLUE}# sing-box Hysteria${NC}"
echo -e "  systemctl status celery-worker      ${BLUE}# Сбор трафика${NC}"
echo -e "  systemctl status celery-beat        ${BLUE}# Планировщик задач${NC}"
echo ""
echo -e "${YELLOW}Логи:${NC}"
echo -e "  journalctl -u xray-panel-api -f     ${BLUE}# Логи API${NC}"
echo -e "  journalctl -u celery-worker -f      ${BLUE}# Логи сбора трафика${NC}"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo -e "  1. Зайдите на https://$DOMAIN"
echo -e "  2. Войдите как admin / admin123"
echo -e "  3. ${RED}ОБЯЗАТЕЛЬНО смените пароль!${NC}"
echo -e "  4. Добавьте ноды используя API Key выше"
echo ""

# Сохранение информации в файл
cat > /root/xray-panel-info.txt << EOF
Xray Panel - Информация об установке
=====================================

URL: https://$DOMAIN
Логин: admin
Пароль: admin123

API Key: $API_KEY
Secret Key: $SECRET_KEY

Database: $DATABASE_URL
EOF

if [ "$USE_POSTGRES" = true ]; then
    echo "PostgreSQL Password: $DB_PASSWORD" >> /root/xray-panel-info.txt
fi

echo -e "${GREEN}Информация сохранена в /root/xray-panel-info.txt${NC}"
echo ""
