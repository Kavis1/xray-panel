#!/bin/bash
# Xray Panel CLI - Management Tool
# Version: 1.0.0

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

INSTALL_DIR="/root/panel"
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
    echo -e "${BLUE}=== Проверка целостности панели ===${NC}"
    echo ""
    
    local errors=0
    
    # Проверка директории
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}✗${NC} Директория панели не найдена: $INSTALL_DIR"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} Директория панели найдена"
    fi
    
    # Проверка backend
    if [ ! -d "$INSTALL_DIR/backend" ]; then
        echo -e "${RED}✗${NC} Backend не найден"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} Backend найден"
    fi
    
    # Проверка базы данных
    if [ ! -f "$INSTALL_DIR/backend/panel.db" ]; then
        echo -e "${RED}✗${NC} База данных не найдена"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} База данных найдена"
    fi
    
    # Проверка venv
    if [ ! -d "$INSTALL_DIR/backend/venv" ]; then
        echo -e "${RED}✗${NC} Virtual environment не найден"
        ((errors++))
    else
        echo -e "${GREEN}✓${NC} Virtual environment найден"
    fi
    
    # Проверка сервисов
    local services=("xray-panel-api" "xray-panel" "singbox-panel" "celery-worker" "celery-beat")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service.service"; then
            echo -e "${GREEN}✓${NC} $service.service запущен"
        else
            echo -e "${RED}✗${NC} $service.service не запущен"
            ((errors++))
        fi
    done
    
    echo ""
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}Все проверки пройдены!${NC}"
    else
        echo -e "${RED}Найдено $errors ошибок${NC}"
    fi
}

# Переустановить панель
reinstall() {
    echo -e "${YELLOW}=== Переустановка панели ===${NC}"
    echo ""
    echo -e "${RED}ВНИМАНИЕ!${NC} Будут удалены все файлы панели."
    echo "База данных и конфигурация будут сохранены."
    echo ""
    read -p "Продолжить? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Отменено"
        return
    fi
    
    # Сохранить данные
    echo "Сохранение данных..."
    mkdir -p /tmp/xraypanel-backup
    cp "$INSTALL_DIR/backend/panel.db" /tmp/xraypanel-backup/ 2>/dev/null || true
    cp "$INSTALL_DIR/backend/.env" /tmp/xraypanel-backup/ 2>/dev/null || true
    
    # Остановить сервисы
    echo "Остановка сервисов..."
    systemctl stop xray-panel-api xray-panel singbox-panel celery-worker celery-beat 2>/dev/null || true
    
    # Удалить файлы (кроме данных)
    echo "Удаление файлов..."
    rm -rf "$INSTALL_DIR/backend/app"
    rm -rf "$INSTALL_DIR/backend/alembic"
    rm -rf "$INSTALL_DIR/backend/venv"
    rm -f "$INSTALL_DIR/backend/requirements.txt"
    
    # Скачать и запустить install.sh
    echo "Загрузка установщика..."
    cd /tmp
    curl -s "https://api.github.com/repos/Kavis1/xray-panel/contents/deployment/panel/install.sh" | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" > install.sh
    chmod +x install.sh
    
    echo "Запуск установки..."
    ./install.sh
    
    # Восстановить данные
    echo "Восстановление данных..."
    cp /tmp/xraypanel-backup/panel.db "$INSTALL_DIR/backend/" 2>/dev/null || true
    cp /tmp/xraypanel-backup/.env "$INSTALL_DIR/backend/" 2>/dev/null || true
    rm -rf /tmp/xraypanel-backup
    
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
    
    # Сохранить данные
    echo "Сохранение данных..."
    mkdir -p /tmp/xraypanel-backup
    cp "$INSTALL_DIR/backend/panel.db" /tmp/xraypanel-backup/
    cp "$INSTALL_DIR/backend/.env" /tmp/xraypanel-backup/
    
    # Скачать install.sh с UPDATE_MODE
    cd /tmp
    curl -s "https://api.github.com/repos/Kavis1/xray-panel/contents/deployment/panel/install.sh" | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" > install.sh
    chmod +x install.sh
    
    echo "Обновление..."
    UPDATE_MODE=true ./install.sh
    
    # Восстановить данные
    cp /tmp/xraypanel-backup/panel.db "$INSTALL_DIR/backend/"
    cp /tmp/xraypanel-backup/.env "$INSTALL_DIR/backend/"
    rm -rf /tmp/xraypanel-backup
    
    # Сохранить новую версию
    echo "$latest" > "$CURRENT_VERSION_FILE"
    
    echo -e "${GREEN}Обновление завершено!${NC}"
}

# Удалить панель
uninstall() {
    echo -e "${RED}=== Удаление панели ===${NC}"
    echo ""
    echo -e "${RED}ВНИМАНИЕ!${NC} Будут удалены ВСЕ файлы панели, включая базу данных!"
    echo ""
    read -p "Вы УВЕРЕНЫ? Введите 'DELETE' для подтверждения: " confirm
    
    if [ "$confirm" != "DELETE" ]; then
        echo "Отменено"
        return
    fi
    
    echo "Остановка сервисов..."
    systemctl stop xray-panel-api xray-panel singbox-panel celery-worker celery-beat 2>/dev/null || true
    systemctl disable xray-panel-api xray-panel singbox-panel celery-worker celery-beat 2>/dev/null || true
    
    echo "Удаление systemd units..."
    rm -f /etc/systemd/system/xray-panel-api.service
    rm -f /etc/systemd/system/xray-panel.service
    rm -f /etc/systemd/system/singbox-panel.service
    rm -f /etc/systemd/system/celery-worker.service
    rm -f /etc/systemd/system/celery-beat.service
    systemctl daemon-reload
    
    echo "Удаление файлов..."
    rm -rf "$INSTALL_DIR"
    
    echo "Удаление CLI..."
    rm -f /usr/local/bin/xraypanel
    
    echo -e "${GREEN}Панель полностью удалена${NC}"
}

# Главное меню
show_menu() {
    clear
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     Xray Panel - Management Tool      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Версия: ${BLUE}$(get_current_version)${NC}"
    echo ""
    echo "1. Проверить целостность"
    echo "2. Переустановить"
    echo "3. Проверить обновления"
    echo "4. Удалить панель"
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
    echo -e "${RED}Запустите от root: sudo xraypanel${NC}"
    exit 1
fi

while true; do
    show_menu
done
