#!/bin/bash
# Check panel health

echo "=== PANEL HEALTH CHECK ==="
echo ""

# 1. Backend
echo "[1/4] Backend..."
if systemctl is-active --quiet xray-panel-backend; then
    echo "  ✓ Service: RUNNING"
    if curl -s http://127.0.0.1:8000/ | grep -q "Xray Control Panel"; then
        echo "  ✓ API: RESPONDING"
    else
        echo "  ✗ API: NOT RESPONDING"
    fi
else
    echo "  ✗ Service: STOPPED"
fi

# 2. Nginx
echo ""
echo "[2/4] Nginx..."
if systemctl is-active --quiet nginx; then
    echo "  ✓ Service: RUNNING"
    if curl -s -I https://localhost 2>&1 | grep -q "200 OK"; then
        echo "  ✓ HTTPS: WORKING"
    else
        echo "  ✗ HTTPS: NOT WORKING"
    fi
else
    echo "  ✗ Service: STOPPED"
fi

# 3. API через nginx
echo ""
echo "[3/4] API через Nginx..."
response=$(curl -s -o /dev/null -w "%{http_code}" https://jdsshrerwwte.dmevent.de/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{}')
if [ "$response" = "422" ]; then
    echo "  ✓ API доступен (HTTP $response)"
else
    echo "  ✗ API недоступен (HTTP $response)"
fi

# 4. Фронтенд
echo ""
echo "[4/4] Фронтенд..."
if curl -s https://jdsshrerwwte.dmevent.de/ | grep -q "<!DOCTYPE html>"; then
    echo "  ✓ Фронтенд загружается"
else
    echo "  ✗ Фронтенд не загружается"
fi

echo ""
echo "=== ИТОГ ==="
echo "Сайт: https://jdsshrerwwte.dmevent.de"
echo ""
echo "Если сайт не работает в браузере:"
echo "  1. Очистите кэш (Ctrl+Shift+Delete)"
echo "  2. Откройте в режиме инкогнито"
echo "  3. Проверьте консоль браузера (F12)"
