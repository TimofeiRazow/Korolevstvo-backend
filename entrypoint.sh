#!/bin/bash

# Entrypoint script для Flask приложения

# Создаём необходимые директории если их нет
mkdir -p /app/instance /app/static/uploads

# Устанавливаем права
chmod -R 755 /app/instance /app/static/uploads

# Выводим информацию для отладки
echo "🚀 Запуск Flask приложения..."
echo "📁 Проверка директорий:"
ls -la /app/instance || echo "❌ /app/instance не существует"
ls -la /app/static/uploads || echo "❌ /app/static/uploads не существует"

# Запускаем приложение
exec "$@"
