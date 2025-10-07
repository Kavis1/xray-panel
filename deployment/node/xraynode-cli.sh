#!/bin/bash
# Xray Node CLI - Management Tool
# Version: 1.0.0

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

INSTALL_DIR="/opt/xray-panel-node"
REPO_URL="https://github.com/Kavis1/xray-panel"
CURRENT_VERSION_FILE="$INSTALL_DIR/.version"

# Получить текущую версию
get_current_version() {
    if [ -f "$CURRENT_VERSION_FILE" ]; then
        cat "$CURRENT_VERSION_FILE"
    else
        echo "unknown"
    fi
}

# Получить последнюю версию с GitHub
get_latest_version() {
    curl -s "https://api.github.com/repos/Kavis1/xray-panel/commits/main" | grep '"sha"' | head -1 | cut -d'"' -f4 | cut -c1-7
}

# Проверить целостность
check_integrity() {
    echo -e "${BLUE}=== Проверка целостности ноды ===${NC}"
    echo ""
    
    local errors=0
    
    # Проверка директории
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}✗${NC} Директория ноды не найдена: $INSTALL_DIR"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} Директория ноды найдена"
    fi
    
    # Проверка бинарника
    if [ ! -f "$INSTALL_DIR/xray-panel-node" ]; then
        echo -e "${RED}✗${NC} Node Service бинарник не найден"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} Node Service бинарник найден"
    fi
    
    # Проверка конфигов
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        echo -e "${RED}✗${NC} .env файл не найден"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} .env файл найден"
    fi
    
    if [ ! -f "$INSTALL_DIR/xray_config.json" ]; then
        echo -e "${RED}✗${NC} xray_config.json не найден"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} xray_config.json найден"
    fi
    
    # Проверка Xray
    if command -v xray &> /dev/null; then
        echo -e "${GREEN}✓${NC} Xray установлен ($(xray version | head -1))"
    else
        echo -e "${RED}✗${NC} Xray не установлен"
        ((errors++))
    fi
    
    # Проверка sing-box
    if command -v sing-box &> /dev/null; then
        echo -e "${GREEN}✓${NC} sing-box установлен ($(sing-box version | head -1))"
    else
        echo -e "${RED}✗${NC} sing-box не установлен"
        ((errors++))
    fi
    
    # Проверка сервисов
    local services=("xray-node" "singbox-node" "xray-panel-node")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service.service"; then
            echo -e "${GREEN}✓${NC} $service.service запущен"
        else
            echo -e "${RED}✗${NC} $service.service не запущен"
            ((errors++))
        fi
    done
    
    # Проверка портов
    if ss -tlnp | grep -q ":50051"; then
        echo -e "${GREEN}✓${NC} Порт 50051 (gRPC) слушается"
    else
        echo -e "${RED}✗${NC} Порт 50051 не слушается"
        ((errors++))
    fi
    
    echo ""
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}Все проверки пройдены!${NC}"
    else
        echo -e "${RED}Найдено $errors ошибок${NC}"
    fi
}

# Переустановить ноду
reinstall() {
    echo -e "${YELLOW}=== Переустановка ноды ===${NC}"
    echo ""
    echo -e "${RED}ВНИМАНИЕ!${NC} Будут удалены все файлы ноды."
    echo "Конфигурация (.env) будет сохранена."
    echo ""
    read -p "Продолжить? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Отменено"
        return
    fi
    
    # Сохранить данные
    echo "Сохранение конфигурации..."
    mkdir -p /tmp/xraynode-backup
    cp "$INSTALL_DIR/.env" /tmp/xraynode-backup/ 2>/dev/null || true
    cp "$INSTALL_DIR/xray_config.json" /tmp/xraynode-backup/ 2>/dev/null || true
    cp "$INSTALL_DIR/singbox_config.json" /tmp/xraynode-backup/ 2>/dev/null || true
    
    # Остановить сервисы
    echo "Остановка сервисов..."
    systemctl stop xray-node singbox-node xray-panel-node 2>/dev/null || true
    
    # Удалить файлы
    echo "Удаление файлов..."
    rm -rf "$INSTALL_DIR"
    
    # Скачать и запустить install-node.sh
    echo "Загрузка установщика..."
    cd /tmp
    curl -s "https://api.github.com/repos/Kavis1/xray-panel/contents/deployment/node/install-node.sh" | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" > install-node.sh
    chmod +x install-node.sh
    
    echo "Запуск установки..."
    ./install-node.sh
    
    # Восстановить конфиги
    echo "Восстановление конфигурации..."
    cp /tmp/xraynode-backup/.env "$INSTALL_DIR/" 2>/dev/null || true
    cp /tmp/xraynode-backup/xray_config.json "$INSTALL_DIR/" 2>/dev/null || true
    cp /tmp/xraynode-backup/singbox_config.json "$INSTALL_DIR/" 2>/dev/null || true
    rm -rf /tmp/xraynode-backup
    
    # Перезапустить сервисы
    systemctl restart xray-node singbox-node xray-panel-node
    
    echo -e "${GREEN}Переустановка завершена!${NC}"
}

# Проверить обновления
check_updates() {
    echo -e "${BLUE}=== Проверка обновлений ===${NC}"
    echo ""
    
    local current=$(get_current_version)
    echo "Текущая версия: $current"
    
    echo "Проверка последней версии..."
    local latest=$(get_latest_version)
    echo "Последняя версия: $latest"
    echo ""
    
    if [ "$current" = "$latest" ]; then
        echo -e "${GREEN}У вас установлена последняя версия!${NC}"
        return
    fi
    
    echo -e "${YELLOW}Доступна новая версия!${NC}"
    echo ""
    read -p "Обновить до версии $latest? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Отменено"
        return
    fi
    
    # Сохранить конфиги
    echo "Сохранение конфигурации..."
    mkdir -p /tmp/xraynode-backup
    cp "$INSTALL_DIR/.env" /tmp/xraynode-backup/
    cp "$INSTALL_DIR/xray_config.json" /tmp/xraynode-backup/ 2>/dev/null || true
    cp "$INSTALL_DIR/singbox_config.json" /tmp/xraynode-backup/ 2>/dev/null || true
    
    # Скачать install-node.sh
    cd /tmp
    curl -s "https://api.github.com/repos/Kavis1/xray-panel/contents/deployment/node/install-node.sh" | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" > install-node.sh
    chmod +x install-node.sh
    
    echo "Обновление..."
    ./install-node.sh
    
    # Восстановить конфиги
    cp /tmp/xraynode-backup/.env "$INSTALL_DIR/"
    cp /tmp/xraynode-backup/xray_config.json "$INSTALL_DIR/" 2>/dev/null || true
    cp /tmp/xraynode-backup/singbox_config.json "$INSTALL_DIR/" 2>/dev/null || true
    rm -rf /tmp/xraynode-backup
    
    # Сохранить новую версию
    echo "$latest" > "$CURRENT_VERSION_FILE"
    
    echo -e "${GREEN}Обновление завершено!${NC}"
}

# Удалить ноду
uninstall() {
    echo -e "${RED}=== Удаление ноды ===${NC}"
    echo ""
    echo -e "${RED}ВНИМАНИЕ!${NC} Будут удалены ВСЕ файлы ноды!"
    echo ""
    read -p "Вы УВЕРЕНЫ? Введите 'DELETE' для подтверждения: " confirm
    
    if [ "$confirm" != "DELETE" ]; then
        echo "Отменено"
        return
    fi
    
    echo "Остановка сервисов..."
    systemctl stop xray-node singbox-node xray-panel-node 2>/dev/null || true
    systemctl disable xray-node singbox-node xray-panel-node 2>/dev/null || true
    
    echo "Удаление systemd units..."
    rm -f /etc/systemd/system/xray-node.service
    rm -f /etc/systemd/system/singbox-node.service
    rm -f /etc/systemd/system/xray-panel-node.service
    systemctl daemon-reload
    
    echo "Удаление файлов..."
    rm -rf "$INSTALL_DIR"
    
    echo "Удаление бинарников..."
    rm -f /usr/local/bin/xray
    rm -f /usr/bin/sing-box
    
    echo "Удаление CLI..."
    rm -f /usr/local/bin/xraynode
    
    echo -e "${GREEN}Нода полностью удалена${NC}"
}

# Главное меню
show_menu() {
    clear
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      Xray Node - Management Tool      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Версия: ${BLUE}$(get_current_version)${NC}"
    echo ""
    echo "1. Проверить целостность"
    echo "2. Переустановить"
    echo "3. Проверить обновления"
    echo "4. Удалить ноду"
    echo "0. Выход"
    echo ""
    read -p "Выберите действие: " choice
    
    case $choice in
        1)
            check_integrity
            ;;
        2)
            reinstall
            ;;
        3)
            check_updates
            ;;
        4)
            uninstall
            exit 0
            ;;
        0)
            exit 0
            ;;
        *)
            echo -e "${RED}Неверный выбор${NC}"
            ;;
    esac
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Основной цикл
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запустите от root: sudo xraynode${NC}"
    exit 1
fi

while true; do
    show_menu
done
