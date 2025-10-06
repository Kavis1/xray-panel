#!/bin/bash
# Скрипт для создания всех протоколов и тестового пользователя

TOKEN=$(cat /tmp/token.txt)
API_URL="http://localhost:8000/api/v1"

echo "=== Создание Inbounds из шаблонов ==="

# 1. VLESS Reality
echo "1. Создание VLESS Reality..."
curl -s -X POST "$API_URL/templates/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "vless_reality",
    "tag": "vless-reality-test",
    "port": 10443
  }' | jq '.' > /tmp/vless_reality.json

# 2. VLESS WebSocket TLS
echo "2. Создание VLESS WebSocket TLS..."
curl -s -X POST "$API_URL/templates/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "vless_ws_tls",
    "tag": "vless-ws-tls-test",
    "port": 10444
  }' | jq '.' > /tmp/vless_ws.json

# 3. VMess WebSocket
echo "3. Создание VMess WebSocket..."
curl -s -X POST "$API_URL/templates/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "vmess_ws",
    "tag": "vmess-ws-test",
    "port": 10080
  }' | jq '.' > /tmp/vmess_ws.json

# 4. VMess gRPC TLS
echo "4. Создание VMess gRPC TLS..."
curl -s -X POST "$API_URL/templates/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "vmess_grpc_tls",
    "tag": "vmess-grpc-tls-test",
    "port": 10445
  }' | jq '.' > /tmp/vmess_grpc.json

# 5. Trojan TCP TLS
echo "5. Создание Trojan TCP TLS..."
curl -s -X POST "$API_URL/templates/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "trojan_tcp_tls",
    "tag": "trojan-tcp-test",
    "port": 10446
  }' | jq '.' > /tmp/trojan.json

# 6. Shadowsocks
echo "6. Создание Shadowsocks..."
curl -s -X POST "$API_URL/templates/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "shadowsocks",
    "tag": "shadowsocks-test",
    "port": 10388
  }' | jq '.' > /tmp/ss.json

echo ""
echo "=== Создание inbounds в базе ==="

# Создать все inbounds
for file in /tmp/vless_reality.json /tmp/vless_ws.json /tmp/vmess_ws.json /tmp/vmess_grpc.json /tmp/trojan.json /tmp/ss.json; do
  if [ -f "$file" ]; then
    config=$(cat "$file" | jq '.config')
    curl -s -X POST "$API_URL/inbounds/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$config" | jq '.id, .tag, .port'
  fi
done

echo ""
echo "=== Создание тестового пользователя ==="

# Создать пользователя
USER_RESPONSE=$(curl -s -X POST "$API_URL/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_all_protocols",
    "email": "test@protocols.local",
    "status": "ACTIVE",
    "traffic_limit_bytes": 107374182400,
    "description": "Тестовый пользователь для всех протоколов"
  }')

USER_ID=$(echo "$USER_RESPONSE" | jq -r '.id')
echo "Создан пользователь ID: $USER_ID"

echo ""
echo "=== Назначение всех inbounds пользователю ==="

# Получить список всех inbounds
INBOUND_TAGS=$(curl -s "$API_URL/inbounds/" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[].tag')

# Создать массив тегов
TAGS_JSON=$(echo "$INBOUND_TAGS" | jq -R -s -c 'split("\n") | map(select(length > 0))')

# Назначить все inbounds
curl -s -X POST "$API_URL/users/$USER_ID/assign-inbounds" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"inbound_tags\": $TAGS_JSON}" | jq '.'

echo ""
echo "=== Просмотр subscription пользователя ==="
SUB_ID=$(echo "$USER_RESPONSE" | jq -r '.subscription_id')
echo "Subscription ID: $SUB_ID"
echo "URL: https://jdsshrerwwte.dmevent.de/sub/$SUB_ID"

echo ""
echo "✅ Готово! Все протоколы созданы и назначены пользователю test_all_protocols"
