#!/bin/bash
# Full panel restart script

echo "=== FULL PANEL RESTART ==="
echo ""

echo "[1/3] Restarting Backend..."
pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
systemctl restart xray-panel-backend
sleep 3

echo "[2/3] Restarting Nginx..."
systemctl restart nginx
sleep 2

echo "[3/3] Checking status..."
echo ""

if systemctl is-active --quiet xray-panel-backend; then
    echo "✓ Backend: RUNNING"
else
    echo "✗ Backend: FAILED"
fi

if systemctl is-active --quiet nginx; then
    echo "✓ Nginx: RUNNING"
else
    echo "✗ Nginx: FAILED"
fi

echo ""
echo "=== PANEL RESTARTED ==="
echo "Access: https://jdsshrerwwte.dmevent.de"
