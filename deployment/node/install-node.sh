#!/bin/bash

set -e

# VERSION INFO - Updated automatically
SCRIPT_VERSION="v2.0.5"
SCRIPT_DATE="2025-10-08 01:53 UTC"
LAST_CHANGE="Start() now uses restart instead of start to apply config"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Проверка режима работы
UPDATE_MODE=false
if [ -d "/opt/xray-panel-node" ] && [ -f "/opt/xray-panel-node/xray-panel-node" ]; then
    UPDATE_MODE=true
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}  Обнаружена установленная нода${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    echo ""
    echo -e "${BLUE}Версия скрипта: ${GREEN}${SCRIPT_VERSION}${NC} | ${SCRIPT_DATE}${NC}"
    echo -e "${BLUE}Последнее изменение: ${LAST_CHANGE}${NC}"
    echo -e "${BLUE}Режим: ОБНОВЛЕНИЕ${NC}"
    echo ""
else
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}  Xray Panel - Установка Ноды${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo -e "${BLUE}Версия скрипта: ${GREEN}${SCRIPT_VERSION}${NC} | ${SCRIPT_DATE}${NC}"
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
    echo -e "${YELLOW}=== Обновление Node Service ===${NC}"
    echo ""
    
    INSTALL_DIR="/opt/xray-panel-node"
    REPO_URL="https://github.com/Kavis1/xray-panel.git"
    
    echo -e "${BLUE}[1/3]${NC} Загрузка обновлений..."
    cd /tmp
    rm -rf temp_node_update
    git clone -q "$REPO_URL" temp_node_update || {
        echo -e "${RED}Ошибка загрузки обновлений${NC}"
        exit 1
    }
    
    echo -e "${BLUE}[2/3]${NC} Обновление исходников..."
    # Сохраняем конфиги
    cp $INSTALL_DIR/.env /tmp/.env.backup 2>/dev/null || true
    cp $INSTALL_DIR/xray_config.json /tmp/xray_config.backup 2>/dev/null || true
    cp $INSTALL_DIR/singbox_config.json /tmp/singbox_config.backup 2>/dev/null || true
    
    # Обновляем только исходники
    cd $INSTALL_DIR
    cp -r /tmp/temp_node_update/node/* .
    
    # Восстанавливаем конфиги
    cp /tmp/.env.backup .env 2>/dev/null || true
    cp /tmp/xray_config.backup xray_config.json 2>/dev/null || true
    cp /tmp/singbox_config.backup singbox_config.json 2>/dev/null || true
    
    echo -e "${BLUE}[3/3]${NC} Компиляция proto и пересборка..."
    
    # Определить архитектуру
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        PROTOC_ARCH="x86_64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        PROTOC_ARCH="aarch_64"
    else
        echo -e "${RED}Неподдерживаемая архитектура: $ARCH${NC}"
        exit 1
    fi
    
    # Проверить и переустановить protoc если архитектура не совпадает
    NEED_REINSTALL=false
    if command -v protoc &> /dev/null; then
        # Проверить работает ли protoc
        if ! protoc --version &> /dev/null; then
            echo "  → Обнаружен неработающий protoc, переустановка..."
            NEED_REINSTALL=true
            rm -f /usr/local/bin/protoc
            rm -rf /usr/local/include/google
        fi
    else
        NEED_REINSTALL=true
    fi
    
    if [ "$NEED_REINSTALL" = true ]; then
        echo "  → Установка protoc для $ARCH..."
        PROTOC_VERSION="25.1"
        cd /tmp
        wget -q "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-${PROTOC_ARCH}.zip"
        unzip -q -o "protoc-${PROTOC_VERSION}-linux-${PROTOC_ARCH}.zip" -d /usr/local
        rm "protoc-${PROTOC_VERSION}-linux-${PROTOC_ARCH}.zip"
    fi
    
    # Установить protoc плагины
    echo "  → Установка protoc плагинов..."
    /usr/local/go/bin/go install google.golang.org/protobuf/cmd/protoc-gen-go@latest >/dev/null 2>&1
    /usr/local/go/bin/go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest >/dev/null 2>&1
    
    export PATH=$PATH:/root/go/bin:/usr/local/go/bin
    
    # Компилировать proto
    echo "  → Компиляция proto файлов..."
    cd $INSTALL_DIR
    protoc --go_out=. --go_opt=paths=source_relative \
        --go-grpc_out=. --go-grpc_opt=paths=source_relative \
        proto/node.proto || {
        echo -e "${RED}Ошибка компиляции proto${NC}"
        exit 1
    }
    
    # Собрать
    echo "  → Сборка бинарника..."
    /usr/local/go/bin/go mod download >/dev/null 2>&1
    /usr/local/go/bin/go build -o xray-panel-node-new cmd/main.go || {
        echo -e "${RED}Ошибка сборки${NC}"
        exit 1
    }
    
    # Остановить сервис
    systemctl stop xray-panel-node
    
    # Заменить бинарник в ПРАВИЛЬНОМ месте
    cp xray-panel-node-new xray-panel-node
    rm xray-panel-node-new
    
    # Запустить сервис
    systemctl start xray-panel-node
    
    # Установка/обновление CLI утилиты
    echo "Обновление xraynode CLI..."
    curl -s "https://api.github.com/repos/Kavis1/xray-panel/contents/deployment/node/xraynode-cli.sh" | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" > /usr/local/bin/xraynode 2>/dev/null || true
    chmod +x /usr/local/bin/xraynode 2>/dev/null || true
    
    # Обновить версию
    echo "$SCRIPT_VERSION" > .version
    
    # Очистка
    rm -rf /tmp/temp_node_update /tmp/*.backup
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓✓✓ Обновление завершено! ✓✓✓${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo "Статус сервисов:"
    systemctl status xray-node --no-pager -l | head -3
    systemctl status singbox-node --no-pager -l | head -3
    systemctl status xray-panel-node --no-pager -l | head -3
    echo ""
    
    echo -e "${YELLOW}=== Диагностика соединения ===${NC}"
    echo ""
    
    # Проверка API ключа
    echo -n "API Key: "
    grep "^API_KEY=" $INSTALL_DIR/.env | cut -d'=' -f2 | head -c 20
    echo "..."
    
    # Проверка gRPC порта
    echo -n "gRPC Port 50051: "
    if ss -tlnp 2>/dev/null | grep -q ":50051" || netstat -tlnp 2>/dev/null | grep -q ":50051"; then
        echo -e "${GREEN}Listening ✓${NC}"
    else
        echo -e "${RED}NOT Listening ✗${NC}"
    fi
    
    # Проверка IsRunning в коде
    echo -n "IsRunning check: "
    if grep -q "Primary check: systemd" $INSTALL_DIR/pkg/xray/manager.go 2>/dev/null; then
        echo -e "${GREEN}Updated ✓${NC}"
    else
        echo -e "${YELLOW}Old version${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ CLI утилита обновлена!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo -e "Управление нодой: ${BLUE}xraynode${NC}"
    echo ""
    echo -e "${YELLOW}Доступные команды в меню:${NC}"
    echo -e "  1. Проверить целостность"
    echo -e "  2. Переустановить ноду"
    echo -e "  3. Проверить обновления"
    echo -e "  4. Удалить ноду"
    echo ""
    
    echo -e "${GREEN}Node Service обновлён и перезапущен!${NC}"
    echo ""
    echo -e "${BLUE}Если панель показывает 'Stopped', проверьте:${NC}"
    echo -e "  1. API_KEY совпадает с панелью"
    echo -e "  2. Логи: journalctl -u xray-panel-node -n 30"
    echo -e "  3. Соединение к панели: ping <PANEL_IP>"
    echo ""
    
    exit 0
fi

# Получение внешнего IP
EXTERNAL_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "")
if [ -z "$EXTERNAL_IP" ]; then
    echo -e "${RED}Не удалось определить внешний IP автоматически${NC}"
    read -p "Введите внешний IP этого сервера: " EXTERNAL_IP
fi

echo ""
echo -e "${YELLOW}=== Настройка параметров ноды ===${NC}"
echo ""
echo -e "Внешний IP ноды: ${GREEN}$EXTERNAL_IP${NC}"
echo ""

# Название ноды
read -p "Введите название ноды (например: DE-Node-1): " NODE_NAME
if [ -z "$NODE_NAME" ]; then
    NODE_NAME="Node-$(date +%s)"
fi

# Генерация API ключа
API_KEY=$(openssl rand -hex 32)
GRPC_PORT=50051

echo ""
echo -e "${GREEN}✓${NC} Параметры настроены"
echo ""

# SSL Certificate Setup
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}SSL AUTHENTICATION SETUP${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "${YELLOW}Для безопасного подключения к панели требуется SSL сертификат.${NC}"
echo ""
echo -e "${CYAN}ВАЖНО: Выполните следующие шаги:${NC}"
echo ""
echo -e "1. Откройте панель управления в браузере"
echo -e "2. Перейдите в раздел ${GREEN}Nodes → Add Node${NC}"
echo -e "3. Заполните данные ноды:"
echo -e "   ${CYAN}Name:${NC}     $NODE_NAME"
echo -e "   ${CYAN}Address:${NC}  $EXTERNAL_IP"
echo -e "   ${CYAN}API Port:${NC} $GRPC_PORT"
echo -e "   ${CYAN}Protocol:${NC} grpc"
echo -e "   ${CYAN}API Key:${NC}  $API_KEY"
echo -e "4. Нажмите ${GREEN}[Generate API Key]${NC} (автоматически)"
echo -e "5. Нажмите ${GREEN}[Create Node]${NC}"
echo -e "6. ${YELLOW}Скопируйте SSL клиентский сертификат${NC} (все 3 блока)"
echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Вставьте SSL сертификат ниже и нажмите Ctrl+D когда закончите:${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Read multiline SSL certificate input
SSL_CERT=$(cat)

if [ -z "$SSL_CERT" ]; then
    echo -e "${RED}Ошибка: SSL сертификат не введен!${NC}"
    echo -e "${YELLOW}Установка прервана. Запустите скрипт заново.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓${NC} SSL сертификат получен"
echo ""

# Установка зависимостей
echo -e "${YELLOW}[1/6]${NC} Установка системных зависимостей..."

if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get update -qq
    apt-get install -y -qq \
        curl \
        wget \
        unzip \
        jq \
        tar \
        build-essential > /dev/null 2>&1
    
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]]; then
    yum install -y curl wget unzip jq tar gcc make > /dev/null 2>&1
else
    echo -e "${RED}Неподдерживаемая ОС: $OS${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Системные зависимости установлены"

# Установка Xray
echo -e "${YELLOW}[2/6]${NC} Установка Xray-core..."
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install -u root > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Xray-core установлен ($(xray version | head -1))"

# Установка sing-box
echo -e "${YELLOW}[3/6]${NC} Установка sing-box..."
SINGBOX_VERSION="1.12.9"

# Определить архитектуру для sing-box
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        SINGBOX_ARCH="amd64"
        ;;
    aarch64|arm64)
        SINGBOX_ARCH="arm64"
        ;;
    armv7l)
        SINGBOX_ARCH="armv7"
        ;;
    *)
        echo -e "${RED}Неподдерживаемая архитектура: $ARCH${NC}"
        exit 1
        ;;
esac

# Остановить если запущен
systemctl stop singbox-node 2>/dev/null || true

wget -q "https://github.com/SagerNet/sing-box/releases/download/v${SINGBOX_VERSION}/sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}.tar.gz"
tar -xzf "sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}.tar.gz"
cp "sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}/sing-box" /usr/bin/
chmod +x /usr/bin/sing-box
rm -rf "sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}"*
echo -e "${GREEN}✓${NC} sing-box установлен (v${SINGBOX_VERSION})"

# Открытие портов в файрволе
echo -e "${YELLOW}[3.5/6]${NC} Открытие портов в firewall..."
PORTS=(443 7443 8388 10080 50051)

if command -v ufw &> /dev/null; then
    for port in "${PORTS[@]}"; do
        ufw allow $port/tcp >/dev/null 2>&1 || true
    done
    echo -e "${GREEN}✓${NC} Порты открыты через UFW"
elif command -v iptables &> /dev/null; then
    for port in "${PORTS[@]}"; do
        iptables -I INPUT -p tcp --dport $port -j ACCEPT >/dev/null 2>&1 || true
    done
    # Сохранить правила
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save >/dev/null 2>&1 || true
    fi
    echo -e "${GREEN}✓${NC} Порты открыты через iptables"
else
    echo -e "${YELLOW}⚠${NC} Firewall не обнаружен, порты могут быть уже открыты"
fi

# Установка Go (для сборки Node Service)
echo -e "${YELLOW}[4/6]${NC} Установка Go..."
GO_VERSION="1.23.1"

# Определить архитектуру
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        GO_ARCH="amd64"
        ;;
    aarch64|arm64)
        GO_ARCH="arm64"
        ;;
    armv7l)
        GO_ARCH="armv6l"
        ;;
    *)
        echo -e "${RED}Неподдерживаемая архитектура: $ARCH${NC}"
        exit 1
        ;;
esac

if ! command -v go &> /dev/null; then
    echo "Скачивание Go ${GO_VERSION} для ${GO_ARCH}..."
    wget -q "https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz"
    rm -rf /usr/local/go
    tar -C /usr/local -xzf "go${GO_VERSION}.linux-${GO_ARCH}.tar.gz"
    rm "go${GO_VERSION}.linux-${GO_ARCH}.tar.gz"
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
    export PATH=$PATH:/usr/local/go/bin
fi
echo -e "${GREEN}✓${NC} Go установлен ($(/usr/local/go/bin/go version))"

# Создание директорий
INSTALL_DIR="/opt/xray-panel-node"
echo -e "${YELLOW}[5/6]${NC} Установка Node Service..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/ssl
cd $INSTALL_DIR

# Сохранение SSL сертификата
echo "$SSL_CERT" > $INSTALL_DIR/ssl/fullchain.pem

# Извлечение компонентов (certificate, private key, CA)
# Разделяем на 3 файла
csplit -s -f $INSTALL_DIR/ssl/part- $INSTALL_DIR/ssl/fullchain.pem '/-----BEGIN/' '{*}' 2>/dev/null || true

# Определяем какой файл что содержит
if [ -f "$INSTALL_DIR/ssl/part-00" ]; then
    # Первый блок пустой, начинаем с part-01
    CERT_FILE="$INSTALL_DIR/ssl/part-01"
    KEY_FILE="$INSTALL_DIR/ssl/part-02"
    CA_FILE="$INSTALL_DIR/ssl/part-03"
else
    CERT_FILE="$INSTALL_DIR/ssl/part-00"
    KEY_FILE="$INSTALL_DIR/ssl/part-01"
    CA_FILE="$INSTALL_DIR/ssl/part-02"
fi

# Копируем в правильные файлы
[ -f "$CERT_FILE" ] && mv "$CERT_FILE" $INSTALL_DIR/ssl/cert.pem
[ -f "$KEY_FILE" ] && mv "$KEY_FILE" $INSTALL_DIR/ssl/key.pem
[ -f "$CA_FILE" ] && mv "$CA_FILE" $INSTALL_DIR/ssl/ca.pem

# Удаляем временные файлы
rm -f $INSTALL_DIR/ssl/part-* $INSTALL_DIR/ssl/fullchain.pem

echo -e "${GREEN}✓${NC} SSL сертификат сохранен в $INSTALL_DIR/ssl/"

# Загрузка файлов ноды из GitHub
# TODO: Заменить на ваш GitHub репозиторий
REPO_URL="https://github.com/Kavis1/xray-panel"
echo "Загрузка файлов ноды..."
git clone -q "$REPO_URL" temp_clone || {
    echo -e "${RED}Ошибка загрузки файлов. Убедитесь что репозиторий доступен.${NC}"
    exit 1
}

# Копирование только файлов ноды
cp -r temp_clone/node/* .
rm -rf temp_clone

# Сборка Node Service
echo "Сборка Node Service..."
/usr/local/go/bin/go mod download > /dev/null 2>&1
/usr/local/go/bin/go build -o xray-panel-node cmd/main.go

# Создание .env файла
cat > .env << EOF
# Node Configuration
NODE_NAME=$NODE_NAME
NODE_ADDRESS=$EXTERNAL_IP
GRPC_PORT=$GRPC_PORT
API_KEY=$API_KEY

# SSL Configuration
SSL_CERT_FILE=$INSTALL_DIR/ssl/cert.pem
SSL_KEY_FILE=$INSTALL_DIR/ssl/key.pem
SSL_CA_FILE=$INSTALL_DIR/ssl/ca.pem

# Xray Configuration
XRAY_API_HOST=127.0.0.1
XRAY_API_PORT=10085

# sing-box Configuration
SINGBOX_API_HOST=127.0.0.1
SINGBOX_API_PORT=9090
EOF

echo -e "${GREEN}✓${NC} Node Service установлен"

# Создание systemd сервисов
echo -e "${YELLOW}[6/6]${NC} Создание systemd сервисов..."

# 1. Xray для ноды
cat > /etc/systemd/system/xray-node.service << 'XRAYEOF'
[Unit]
Description=Xray Node Proxy Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/xray run -c /opt/xray-panel-node/xray_config.json
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
XRAYEOF

# 2. sing-box для ноды
cat > /etc/systemd/system/singbox-node.service << 'SINGEOF'
[Unit]
Description=sing-box Node Service (Hysteria)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/sing-box run -c /opt/xray-panel-node/singbox_config.json
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SINGEOF

# 3. Node Service (gRPC API)
cat > /etc/systemd/system/xray-panel-node.service << 'NODEEOF'
[Unit]
Description=Xray Panel Node Service (gRPC)
After=network.target xray-node.service singbox-node.service
Wants=xray-node.service singbox-node.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xray-panel-node
EnvironmentFile=/opt/xray-panel-node/.env
ExecStart=/opt/xray-panel-node/xray-panel-node
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
NODEEOF

# Создание начальных конфигов
# Базовый Xray конфиг с Stats API
cat > /opt/xray-panel-node/xray_config.json << 'XRAYJSON'
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
cat > /opt/xray-panel-node/singbox_config.json << 'SINGJSON'
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

# Настройка firewall (открытие портов)
echo "Настройка firewall..."

# 1. iptables (работает ВСЕГДА, особенно важно для Oracle Cloud)
echo "Открытие портов в iptables..."
iptables -C INPUT -p tcp --dport $GRPC_PORT -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport $GRPC_PORT -j ACCEPT
iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 443 -j ACCEPT
iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 80 -j ACCEPT

# Сохранить правила iptables
if command -v netfilter-persistent &> /dev/null; then
    netfilter-persistent save > /dev/null 2>&1
elif [ -d /etc/iptables ]; then
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
elif [ -f /etc/sysconfig/iptables ]; then
    iptables-save > /etc/sysconfig/iptables 2>/dev/null || true
fi

# 2. UFW (если используется)
if command -v ufw &> /dev/null; then
    ufw allow $GRPC_PORT/tcp comment "Xray Panel Node gRPC" > /dev/null 2>&1 || true
    ufw allow 443/tcp comment "HTTPS" > /dev/null 2>&1 || true
    ufw allow 80/tcp comment "HTTP" > /dev/null 2>&1 || true
fi

# 3. firewalld (если используется)
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=$GRPC_PORT/tcp > /dev/null 2>&1 || true
    firewall-cmd --permanent --add-port=443/tcp > /dev/null 2>&1 || true
    firewall-cmd --permanent --add-port=80/tcp > /dev/null 2>&1 || true
    firewall-cmd --reload > /dev/null 2>&1 || true
fi

echo -e "${GREEN}✓${NC} Порты открыты: $GRPC_PORT, 443, 80"

# Reload systemd
systemctl daemon-reload

# Запуск сервисов
systemctl enable xray-node.service
systemctl start xray-node.service

systemctl enable singbox-node.service
systemctl start singbox-node.service

systemctl enable xray-panel-node.service
systemctl start xray-panel-node.service

echo -e "${GREEN}✓${NC} Сервисы запущены"

# Проверка статуса
sleep 3
ALL_RUNNING=true

if ! systemctl is-active --quiet xray-node.service; then
    echo -e "${RED}✗${NC} xray-node.service не запущен"
    ALL_RUNNING=false
fi

if ! systemctl is-active --quiet singbox-node.service; then
    echo -e "${RED}✗${NC} singbox-node.service не запущен"
    ALL_RUNNING=false
fi

if ! systemctl is-active --quiet xray-panel-node.service; then
    echo -e "${RED}✗${NC} xray-panel-node.service не запущен"
    ALL_RUNNING=false
fi

echo ""
echo -e "${BLUE}=========================================${NC}"
if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✓✓✓ Установка ноды завершена! ✓✓✓${NC}"
else
    echo -e "${YELLOW}⚠ Установка завершена с предупреждениями${NC}"
fi
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  ДАННЫЕ ДЛЯ ПОДКЛЮЧЕНИЯ К ПАНЕЛИ       ║${NC}"
echo -e "${YELLOW}╠════════════════════════════════════════╣${NC}"
echo -e "${YELLOW}║${NC}                                        ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${GREEN}Название:${NC}  $NODE_NAME"
echo -e "${YELLOW}║${NC}  ${GREEN}IP адрес:${NC}  $EXTERNAL_IP"
echo -e "${YELLOW}║${NC}  ${GREEN}API Port:${NC}  $GRPC_PORT"
echo -e "${YELLOW}║${NC}  ${GREEN}Protocol:${NC}  grpc"
echo -e "${YELLOW}║${NC}  ${GREEN}API Key:${NC}   $API_KEY"
echo -e "${YELLOW}║${NC}                                        ${YELLOW}║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${RED}▶ СОХРАНИТЕ ЭТИ ДАННЫЕ!${NC}"
echo -e "${RED}▶ Используйте их для добавления ноды в панель${NC}"
echo ""
echo -e "${YELLOW}Управление сервисами:${NC}"
echo -e "  systemctl status xray-node              ${BLUE}# Xray прокси${NC}"
echo -e "  systemctl status singbox-node           ${BLUE}# sing-box Hysteria${NC}"
echo -e "  systemctl status xray-panel-node        ${BLUE}# Node Service (gRPC)${NC}"
echo ""
echo -e "  systemctl restart xray-node             ${BLUE}# Перезапуск Xray${NC}"
echo -e "  systemctl restart singbox-node          ${BLUE}# Перезапуск sing-box${NC}"
echo -e "  systemctl restart xray-panel-node       ${BLUE}# Перезапуск Node Service${NC}"
echo ""

# Установка CLI утилиты
echo "Установка xraynode CLI..."
curl -s "https://api.github.com/repos/Kavis1/xray-panel/contents/deployment/node/xraynode-cli.sh" | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" > /usr/local/bin/xraynode 2>/dev/null || true
chmod +x /usr/local/bin/xraynode 2>/dev/null || true

# Сохранить версию
echo "$SCRIPT_VERSION" > /opt/xray-panel-node/.version

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ CLI утилита установлена!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "Управление нодой: ${BLUE}xraynode${NC}"
echo ""
echo -e "${YELLOW}Доступные команды в меню:${NC}"
echo -e "  1. Проверить целостность"
echo -e "  2. Переустановить ноду"
echo -e "  3. Проверить обновления"
echo -e "  4. Удалить ноду"
echo ""

echo -e "${YELLOW}Логи:${NC}"
echo -e "  journalctl -u xray-node -f              ${BLUE}# Логи Xray${NC}"
echo -e "  journalctl -u singbox-node -f           ${BLUE}# Логи sing-box${NC}"
echo -e "  journalctl -u xray-panel-node -f        ${BLUE}# Логи Node Service${NC}"
echo ""
echo -e "${YELLOW}Конфигурационные файлы:${NC}"
echo -e "  /opt/xray-panel-node/.env               ${BLUE}# Настройки ноды${NC}"
echo -e "  /opt/xray-panel-node/xray_config.json   ${BLUE}# Конфиг Xray${NC}"
echo -e "  /opt/xray-panel-node/singbox_config.json ${BLUE}# Конфиг sing-box${NC}"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo -e "  1. Скопируйте данные подключения выше"
echo -e "  2. Войдите в панель управления"
echo -e "  3. Перейдите в раздел 'Nodes' → 'Add Node'"
echo -e "  4. Введите данные и нажмите 'Connect'"
echo -e "  5. Нода начнёт передавать статистику на панель"
echo ""

# Сохранение информации в файл
cat > /root/xray-node-info.txt << EOF
Xray Panel Node - Информация об установке
==========================================

Название: $NODE_NAME
IP адрес: $EXTERNAL_IP
API Port: $GRPC_PORT
Protocol: grpc
API Key:  $API_KEY

Установлено:
- Xray-core: $(xray version 2>&1 | head -1)
- sing-box: v${SINGBOX_VERSION}
- Go: $(/usr/local/go/bin/go version)

Директория: /opt/xray-panel-node
Конфигурация: /opt/xray-panel-node/.env

Сервисы:
- xray-node.service          (Xray прокси)
- singbox-node.service       (sing-box Hysteria)
- xray-panel-node.service    (Node gRPC API)

$(date)
EOF

echo -e "${GREEN}Информация сохранена в /root/xray-node-info.txt${NC}"
echo ""
