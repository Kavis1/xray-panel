#!/bin/bash
echo "=== Перезапуск всех сервисов Xray Panel ==="

# Остановка
echo "Остановка старых процессов..."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "./node" 2>/dev/null  
pkill -f "vite" 2>/dev/null
sleep 3

# Backend
echo "Запуск Backend..."
cd /root/panel/backend
nohup ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 2

# Node
echo "Запуск Node..."
export PATH=$PATH:/usr/local/go/bin
cd /root/panel/node
nohup ./node > /tmp/node.log 2>&1 &
sleep 2

# Frontend
echo "Запуск Frontend..."
cd /root/panel/frontend
nohup npm run dev -- --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
sleep 3

# Nginx
echo "Перезапуск Nginx..."
systemctl restart nginx

echo ""
echo "=== Проверка статуса ==="
ps aux | grep -E "uvicorn|node.*xray-panel|vite" | grep -v grep
echo ""
echo "✓ Все сервисы перезапущены"
echo "Логи: /tmp/backend.log, /tmp/node.log, /tmp/frontend.log"
