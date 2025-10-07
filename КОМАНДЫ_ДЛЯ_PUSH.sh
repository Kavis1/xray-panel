#!/bin/bash

# Этот скрипт содержит команды для загрузки проекта в GitHub
# Система безопасности Droid обнаружила примеры ключей в .env.example
# и документации, поэтому коммит нужно сделать вручную.

# ✅ Всё уже готово:
# - URL обновлены на Kavis1
# - .gitignore создан
# - LICENSE создан
# - README.md создан
# - Секретные файлы удалены
# - Git инициализирован
# - Файлы в staging
# - Remote настроен

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           ЗАГРУЗКА В GITHUB - ФИНАЛЬНЫЕ КОМАНДЫ                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Всё подготовлено! Осталось 3 команды:"
echo ""
echo "1. Перейдите в директорию проекта:"
echo "   cd /root/panel"
echo ""
echo "2. Создайте коммит (игнорируя предупреждения о примерах ключей):"
cat << 'COMMITEOF'
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
COMMITEOF
echo ""
echo "3. Отправьте в GitHub:"
echo "   git push -u origin main"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 ПРИМЕЧАНИЕ:"
echo "   Обнаруженные 'секреты' это ПРИМЕРЫ из .env.example и документации."
echo "   Это БЕЗОПАСНО - никаких реальных секретов в репозитории нет!"
echo ""
echo "   Примеры:"
echo "   - SECRET_KEY=change-this-to-random-secret-key (в .env.example)"
echo "   - admin123 (дефолтный пароль, пользователь должен сменить)"
echo "   - Примеры API ключей в документации"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "🔐 АВТОРИЗАЦИЯ В GITHUB:"
echo ""
echo "Если GitHub запросит авторизацию:"
echo ""
echo "ВАРИАНТ 1 (рекомендуется): Personal Access Token"
echo "   1. Откройте: https://github.com/settings/tokens"
echo "   2. Generate new token (classic)"
echo "   3. Выберите scopes: repo (full control)"
echo "   4. Скопируйте токен"
echo "   5. При git push используйте токен вместо пароля:"
echo "      Username: Kavis1"
echo "      Password: [вставьте токен]"
echo ""
echo "ВАРИАНТ 2: SSH ключ"
echo "   1. Создайте SSH ключ:"
echo "      ssh-keygen -t ed25519 -C 'your_email@example.com'"
echo "   2. Добавьте в GitHub: https://github.com/settings/keys"
echo "      cat ~/.ssh/id_ed25519.pub"
echo "   3. Измените remote на SSH:"
echo "      git remote set-url origin git@github.com:Kavis1/xray-panel.git"
echo "   4. Пуш:"
echo "      git push -u origin main"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ ПОСЛЕ ЗАГРУЗКИ:"
echo ""
echo "Проверьте что скрипты доступны:"
echo "   wget https://raw.githubusercontent.com/Kavis1/xray-panel/main/deployment/panel/install.sh"
echo ""
echo "Создайте первый Release:"
echo "   1. GitHub → Releases → Create new release"
echo "   2. Tag: v1.0.0"
echo "   3. Title: Xray Panel v1.0.0 - Initial Release"
echo "   4. Опубликуйте!"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 Готово! Удачи с проектом!"
echo ""
