#!/bin/bash
echo "================================================"
echo "  Запуск Xray Panel"
echo "================================================"

cd /root/panel/backend

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация
source venv/bin/activate

# Проверка зависимостей
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Установка зависимостей..."
    pip install -q -r requirements.txt
fi

# Проверка базы данных
if [ ! -f "panel.db" ]; then
    echo "Инициализация базы данных..."
    alembic upgrade head
fi

# Остановка старого процесса
pkill -f "uvicorn app.main:app" 2>/dev/null

# Запуск
echo "Запуск сервера на http://localhost:8000"
echo "Документация: http://localhost:8000/docs"
echo "Логин: admin / admin123"
echo ""

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/panel.log 2>&1 &

sleep 3

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Панель запущена успешно!"
    echo ""
    echo "Для просмотра логов: tail -f /tmp/panel.log"
    echo "Для остановки: pkill -f 'uvicorn app.main:app'"
else
    echo "❌ Ошибка запуска. Проверьте логи: cat /tmp/panel.log"
fi

echo "================================================"
