#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}  Обновление Node Service${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""

# Проверка что нода установлена
if [ ! -d "/opt/xray-panel-node" ]; then
    echo -e "${RED}Нода не установлена! Сначала установите ноду.${NC}"
    exit 1
fi

INSTALL_DIR="/opt/xray-panel-node"
REPO_URL="https://github.com/Kavis1/xray-panel.git"

echo -e "${BLUE}[1/4]${NC} Загрузка обновлений..."
cd /tmp
rm -rf temp_node_update
git clone -q "$REPO_URL" temp_node_update || {
    echo -e "${RED}Ошибка загрузки обновлений${NC}"
    exit 1
}

echo -e "${BLUE}[2/4]${NC} Создание резервных копий..."
cp $INSTALL_DIR/.env /tmp/.env.backup 2>/dev/null || true
cp $INSTALL_DIR/xray_config.json /tmp/xray_config.backup 2>/dev/null || true
cp $INSTALL_DIR/singbox_config.json /tmp/singbox_config.backup 2>/dev/null || true

echo -e "${BLUE}[3/4]${NC} Обновление исходников..."
cd $INSTALL_DIR
cp -r /tmp/temp_node_update/node/* .

# Восстанавливаем конфиги
cp /tmp/.env.backup .env 2>/dev/null || true
cp /tmp/xray_config.backup xray_config.json 2>/dev/null || true
cp /tmp/singbox_config.backup singbox_config.json 2>/dev/null || true

echo -e "${BLUE}[4/4]${NC} Пересборка и перезапуск..."

# Пересборка
export PATH=$PATH:/usr/local/go/bin
/usr/local/go/bin/go build -o xray-panel-node-new cmd/main.go || {
    echo -e "${RED}Ошибка сборки${NC}"
    exit 1
}

# Остановить сервис
systemctl stop xray-panel-node 2>/dev/null || true

# Заменить бинарник
cp xray-panel-node-new /usr/local/bin/xray-panel-node
rm xray-panel-node-new

# Запустить сервис
systemctl start xray-panel-node

# Очистка
rm -rf /tmp/temp_node_update /tmp/*.backup

sleep 2

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✓✓✓ Обновление завершено! ✓✓✓${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Статус сервисов:"
systemctl status xray-node --no-pager -l | head -3
systemctl status singbox-node --no-pager -l | head -3
systemctl status xray-panel-node --no-pager -l | head -3
echo ""
echo -e "${GREEN}Node Service обновлён с исправлениями!${NC}"
echo -e "${GREEN}Через 1-2 минуты панель покажет: Xray Running${NC}"
