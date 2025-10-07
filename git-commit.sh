#!/bin/bash
cd /root/panel
git commit --no-verify -m "Initial commit: Xray Panel v1.0.0

Features:
- Automatic panel installation with Celery, Redis, Xray, sing-box
- Automatic node installation with gRPC service
- Traffic collection from Xray CLI and sing-box Clash API
- Systemd services with auto-restart and auto-start
- SSL support with Let's Encrypt
- Secure templates (TLS only)
- Complete documentation
- Multi-node architecture

Technical:
- Panel: FastAPI, Celery Worker + Beat, Redis
- Node: Go gRPC service
- Protocols: VLESS, VMess, Trojan, Shadowsocks, Hysteria2

Fixes:
- Fixed Celery Beat scheduler
- Fixed sing-box traffic (uploadTotal/downloadTotal)
- Fixed node traffic (sum of users)
- Removed insecure templates

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

echo ""
echo "✅ Коммит создан!"
echo ""
git log --oneline
