#!/bin/bash
# Safe backend restart script

echo "=== Restarting Xray Panel Backend ==="

# Kill all uvicorn processes
echo "Stopping old processes..."
pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Restart via systemd
echo "Starting backend service..."
systemctl restart xray-panel-backend

# Wait for startup
sleep 3

# Check status
if systemctl is-active --quiet xray-panel-backend; then
    echo "✓ Backend is running"
    systemctl status xray-panel-backend --no-pager -l | head -10
else
    echo "✗ Backend failed to start"
    journalctl -u xray-panel-backend -n 20 --no-pager
    exit 1
fi
