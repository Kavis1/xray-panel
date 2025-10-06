# Чеклист перед загрузкой в GitHub

## ✅ Что уже готово

### Deployment скрипты
- ✅ `deployment/panel/install.sh` - установка панели
- ✅ `deployment/node/install-node.sh` - установка ноды
- ✅ `deployment/panel/README.md` - документация панели
- ✅ `deployment/node/README.md` - документация ноды
- ✅ `deployment/README.md` - общая документация
- ✅ `deployment/STRUCTURE.md` - структура файлов

### Проверенные исправления
- ✅ Celery Worker + Beat (оба в systemd)
- ✅ Redis установка и настройка
- ✅ Xray Stats API на порту 10085
- ✅ sing-box Clash API на порту 9090
- ✅ Сбор трафика: Xray CLI + sing-box uploadTotal/downloadTotal
- ✅ Трафик ноды = сумма трафика всех юзеров
- ✅ Безопасные шаблоны (только с TLS)

## ⚠️ Что нужно проверить

### 1. backend/requirements.txt
```bash
# Проверьте что есть requests
grep "requests" /root/panel/backend/requirements.txt
```
**Ожидаемый вывод:** `requests==2.31.0`

### 2. backend/app/workers/tasks.py
```bash
# Проверьте функцию сбора трафика
grep -A 5 "uploadTotal" /root/panel/backend/app/workers/tasks.py
```
**Должно быть:** использование `uploadTotal` и `downloadTotal` из sing-box

### 3. backend/app/services/inbound/templates.py
```bash
# Проверьте что нет небезопасных шаблонов
grep -i "without.*tls" /root/panel/backend/app/services/inbound/templates.py
```
**Не должно быть:** "without TLS", "insecure"

### 4. Проверка скриптов
```bash
# Проверьте что скрипты исполняемые
ls -l /root/panel/deployment/panel/install.sh
ls -l /root/panel/deployment/node/install-node.sh
```
**Ожидаемый вывод:** `-rwxr-xr-x` (executable)

## 🔧 Что нужно сделать

### 1. Обновить URL в скриптах

#### В install.sh
```bash
# Откройте файл
nano /root/panel/deployment/panel/install.sh

# Найдите строку:
REPO_URL="https://github.com/YOUR_USERNAME/xray-panel"

# Замените YOUR_USERNAME на ваш GitHub username
```

#### В install-node.sh
```bash
# Откройте файл
nano /root/panel/deployment/node/install-node.sh

# Найдите строку:
REPO_URL="https://github.com/YOUR_USERNAME/xray-panel"

# Замените YOUR_USERNAME на ваш GitHub username
```

### 2. Создать .gitignore

```bash
cat > /root/panel/.gitignore << 'GITEOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/
ENV/
*.egg-info/
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3
panel.db

# Environment
.env
*.env
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/
celerybeat-schedule
celerybeat-schedule.db

# OS
.DS_Store
Thumbs.db
.directory

# Node
node_modules/
npm-debug.log
yarn-error.log

# Go
*.exe
*.dll
*.so
*.dylib
vendor/
node/node
node/xray-panel-node

# Temporary
tmp/
temp/
*.tmp
nohup.out

# Xray/sing-box runtime
xray_config.json
singbox_config.json
GITEOF
```

### 3. Создать LICENSE

```bash
cat > /root/panel/LICENSE << 'LICEOF'
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
LICEOF
```

### 4. Создать главный README.md

```bash
cp /root/panel/deployment/README.md /root/panel/README.md
```

Затем отредактируйте и добавьте в начало:

```markdown
# Xray Panel

Современная панель управления для Xray VPN с автоматической установкой и поддержкой множественных нод.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[... остальной контент из deployment/README.md ...]
```

## 📦 Подготовка к загрузке

### Удалить ненужные файлы

```bash
cd /root/panel

# Удалить базу данных (будет создана при установке)
rm -f backend/panel.db backend/*.db

# Удалить .env (есть .env.example)
rm -f backend/.env node/.env

# Удалить Python кеш
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete

# Удалить venv
rm -rf backend/venv

# Удалить Celery schedule
rm -f backend/celerybeat-schedule*

# Удалить скомпилированную ноду
rm -f node/node node/xray-panel-node

# Удалить временные файлы
rm -f nohup.out
rm -rf node/github.com
```

### Проверить что осталось

```bash
cd /root/panel
tree -L 2 -I 'venv|__pycache__|*.pyc|node_modules'
```

## 🚀 Загрузка в GitHub

```bash
cd /root/panel

# Инициализация git
git init

# Добавить файлы
git add .

# Проверить что будет закоммичено
git status

# Создать коммит
git commit -m "Initial commit: Xray Panel v1.0.0

Features:
- Automatic panel installation with Celery, Redis, Xray, sing-box
- Automatic node installation with gRPC service
- Traffic collection from Xray CLI and sing-box Clash API
- Systemd services with auto-restart
- SSL support with Let's Encrypt
- Secure templates (TLS only)
- Complete documentation

Fixes:
- Fixed Celery Beat scheduler integration
- Fixed sing-box traffic collection (uploadTotal/downloadTotal)
- Fixed node traffic calculation (sum of all users)
- Added requests library for Clash API
- Removed insecure templates (non-TLS)"

# Добавить remote (ЗАМЕНИТЕ YOUR_USERNAME!)
git remote add origin https://github.com/YOUR_USERNAME/xray-panel.git

# Отправить
git branch -M main
git push -u origin main
```

## ✅ После загрузки

### 1. Проверить доступность скриптов

```bash
# Панель
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh

# Нода
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/node/install-node.sh
```

### 2. Создать Release

В GitHub:
1. Перейдите в Releases → Create new release
2. Tag: `v1.0.0`
3. Title: `Xray Panel v1.0.0 - Initial Release`
4. Description:
```markdown
## 🎉 First Release

Complete Xray Panel management system with automatic deployment.

### Features
- ✅ One-command installation for panel and nodes
- ✅ Automatic SSL with Let's Encrypt
- ✅ Traffic collection from Xray and sing-box
- ✅ Systemd services with auto-restart
- ✅ Multiple protocol support (VLESS, VMess, Trojan, Hysteria2)
- ✅ Multi-node architecture
- ✅ Complete REST API

### Installation

**Panel:**
\`\`\`bash
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh
chmod +x install.sh
sudo ./install.sh
\`\`\`

**Node:**
\`\`\`bash
wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/node/install-node.sh
chmod +x install-node.sh
sudo ./install-node.sh
\`\`\`

See [documentation](https://github.com/YOUR_USERNAME/xray-panel/tree/main/deployment) for details.
```

### 3. Обновить README

Добавьте в начало главного README.md:
- Скриншоты (если есть)
- Ссылку на demo (если есть)
- Статус билда (если используете CI/CD)

## 🧪 Тестирование

### Тест на чистой Ubuntu 22.04

#### Панель
```bash
# 1. Создайте VM с Ubuntu 22.04
# 2. Настройте DNS (A-запись на IP)
# 3. Запустите:

wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/panel/install.sh
chmod +x install.sh
sudo ./install.sh

# Следуйте инструкциям
# Проверьте что все сервисы запустились
systemctl status xray-panel-api celery-worker celery-beat

# Откройте в браузере
https://ваш-домен
```

#### Нода
```bash
# 1. Создайте VM с Ubuntu 22.04
# 2. Запустите:

wget https://raw.githubusercontent.com/YOUR_USERNAME/xray-panel/main/deployment/node/install-node.sh
chmod +x install-node.sh
sudo ./install-node.sh

# Скопируйте данные подключения
cat /root/xray-node-info.txt

# Добавьте в панель через Web UI
# Проверьте что все сервисы работают
systemctl status xray-panel-node xray-node singbox-node
```

## 📋 Финальный чеклист

Перед push в GitHub убедитесь:

- [ ] `requirements.txt` содержит `requests==2.31.0`
- [ ] `tasks.py` использует `uploadTotal/downloadTotal`
- [ ] `templates.py` содержит только безопасные шаблоны
- [ ] URL в скриптах обновлены на ваш GitHub username
- [ ] `.gitignore` создан
- [ ] `LICENSE` создан
- [ ] Главный `README.md` создан
- [ ] Удалены `.env` файлы с секретами
- [ ] Удалены базы данных
- [ ] Удалены venv и __pycache__
- [ ] Скрипты исполняемые (chmod +x)

## 📚 Дополнительно

### Настройка GitHub Pages (опционально)

Для документации можно создать `docs/` папку и включить GitHub Pages.

### CI/CD (опционально)

Можно добавить GitHub Actions для:
- Проверки синтаксиса Python
- Сборки Go приложения
- Автоматических тестов
- Создания Docker образов

### Docker образы (опционально)

В будущем можно добавить Docker Compose для быстрого развертывания.

---

**Готово к загрузке!** 🚀
