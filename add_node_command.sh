#!/bin/bash
# Скрипт для добавления Node через API панели

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Добавление Node в панель ===${NC}\n"

# Параметры
PANEL_URL="https://jdsshrerwwte.dmevent.de"
ADMIN_USER="admin"
ADMIN_PASS="admin123"
API_KEY="7f8a9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a"
NODE_ADDRESS="85.192.63.87"  # IP вашего сервера

echo -e "${GREEN}1. Получение токена авторизации...${NC}"
TOKEN=$(curl -s -X POST "$PANEL_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Ошибка: Не удалось получить токен${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Токен получен${NC}\n"

echo -e "${GREEN}2. Создание Node...${NC}"
RESPONSE=$(curl -s -X POST "$PANEL_URL/api/v1/nodes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Main Node\",
    \"address\": \"$NODE_ADDRESS\",
    \"api_port\": 50051,
    \"api_protocol\": \"grpc\",
    \"api_key\": \"$API_KEY\",
    \"usage_ratio\": 1.0,
    \"traffic_limit_bytes\": 0,
    \"traffic_notify_percent\": 80,
    \"is_enabled\": true,
    \"add_host_to_inbounds\": true,
    \"view_position\": 0,
    \"country_code\": \"DE\"
  }")

# Проверка результата
if echo "$RESPONSE" | grep -q '"id"'; then
    echo -e "${GREEN}✓ Node успешно создана!${NC}\n"
    echo -e "${YELLOW}Ответ сервера:${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ Ошибка при создании Node${NC}\n"
    echo -e "${YELLOW}Ответ сервера:${NC}"
    echo "$RESPONSE"
    exit 1
fi

echo -e "\n${GREEN}=== Готово! ===${NC}"
echo -e "Node добавлена в панель: ${YELLOW}$PANEL_URL/nodes${NC}"
