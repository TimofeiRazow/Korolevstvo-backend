FROM python:3.11

# Рабочая директория
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Копируем и делаем исполняемым entrypoint скрипт
COPY entrypoint.sh /entrypoint.sh
# Конвертируем Windows line endings в Unix и делаем исполняемым
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Экспонируем порт
EXPOSE 5000

# Используем entrypoint для создания директорий перед запуском
ENTRYPOINT ["/entrypoint.sh"]

# Запуск приложения
CMD ["python", "app.py"]
