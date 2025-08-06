
# run.py (для запуска в продакшене)
import os
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Создание таблиц при первом запуске
        db.create_all()
        
        # Заполнение тестовыми данными
        from seed_data import seed_database
        seed_database()
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )

# seed_data.py (тестовые данные)
from models import db, Service, TeamMember, Portfolio, Review
from datetime import date, datetime

def seed_database():
    """Заполнение базы тестовыми данными"""
    
    # Проверяем, есть ли уже данные
    if Service.query.first():
        return
    
    # Услуги
    services_data = [
        {
            'title': 'Детские праздники',
            'category': 'children',
            'duration': '3-4 часа',
            'min_guests': '10 детей',
            'rating': 5.0,
            'price': 'от 45,000 ₸',
            'price_description': 'базовый пакет',
            'description': 'Яркие и веселые детские праздники с профессиональными аниматорами',
            'features': ['Аниматоры', 'Игры', 'Шоу', 'Подарки'],
            'subcategories': ['Дни рождения', 'Выпускные'],
            'cover_image': 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d',
            'featured': True,
            'tags': ['дети', 'аниматоры', 'веселье'],
            'packages': [
                {'name': 'Базовый', 'price': '45,000 ₸', 'features': ['2 часа', 'Аниматор', 'Игры']}
            ]
        },
        {
            'title': 'Свадебные торжества',
            'category': 'weddings',
            'duration': '6-10 часов',
            'min_guests': '30 человек',
            'rating': 5.0,
            'price': 'от 150,000 ₸',
            'price_description': 'полный день',
            'description': 'Создаем свадьбы мечты от регистрации до банкета',
            'features': ['Ведущий', 'Декор', 'Фото', 'Музыка'],
            'subcategories': ['Регистрация', 'Банкет', 'Фотосессии'],
            'cover_image': 'https://images.unsplash.com/photo-1519741497674-611481863552',
            'featured': True,
            'tags': ['свадьба', 'торжество', 'любовь'],
            'packages': [
                {'name': 'Классическая', 'price': '150,000 ₸', 'features': ['Ведущий', 'Декор', 'Фото']}
            ]
        }
    ]
    
    for service_data in services_data:
        service = Service(**service_data)
        db.session.add(service)
    
    # Команда
    team_data = [
        {
            'name': 'Ольга',
            'role': 'Руководитель агентства',
            'description': 'Основатель и вдохновитель команды',
            'active': True
        },
        {
            'name': 'Елена',
            'role': 'Руководитель и Ведущая',
            'description': 'Координирует все мероприятия',
            'active': True
        }
    ]
    
    for member_data in team_data:
        member = TeamMember(**member_data)
        db.session.add(member)
    
    # Отзывы
    reviews_data = [
        {
            'name': 'Алена',
            'rating': 5,
            'text': 'Здравствуйте😊 хочу сказать Вам большое спасибо! Дети в восторге😄',
            'service_type': 'Детские праздники',
            'approved': True
        },
        {
            'name': 'Марина',
            'rating': 5,
            'text': 'На протяжении последних 5 лет праздничное агентство приносит в жизнь нашей семьи много радости!',
            'service_type': 'Детские праздники',
            'approved': True
        }
    ]
    
    for review_data in reviews_data:
        review = Review(**review_data)
        db.session.add(review)
    
    # Портфолио
    portfolio_data = [
        {
            'title': 'День рождения принцессы Амелии (5 лет)',
            'category': 'children',
            'date': date(2024, 7, 15),
            'location': 'Ресторан "Золотой дракон"',
            'guests': '25 детей',
            'budget': '120,000 ₸',
            'rating': 5,
            'description': 'Волшебный праздник в стиле Disney с аниматорами',
            'tags': ['принцессы', 'disney', 'аниматоры'],
            'cover_image': 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d',
            'featured': True
        },
        {
            'title': 'Свадьба Алексея и Марии',
            'category': 'wedding',
            'date': date(2024, 6, 20),
            'location': 'Загородный комплекс "Весна"',
            'guests': '150 гостей',
            'budget': '850,000 ₸',
            'rating': 5,
            'description': 'Романтическая свадьба в стиле прованс',
            'tags': ['прованс', 'регистрация', 'музыка'],
            'cover_image': 'https://images.unsplash.com/photo-1519741497674-611481863552',
            'featured': True
        }
    ]
    
    for portfolio_item in portfolio_data:
        item = Portfolio(**portfolio_item)
        db.session.add(item)
    
    try:
        db.session.commit()
        print("База данных успешно заполнена тестовыми данными")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при заполнении БД: {e}")

# .env (переменные окружения)
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///korolevstvo_chudes.db

# Email settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@prazdnikvdom.kz

# Gunicorn config (gunicorn.conf.py)
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True

# Docker support (Dockerfile)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]

# Docker Compose (docker-compose.yml)
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/korolevstvo_chudes
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=korolevstvo_chudes
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:

# Nginx config (nginx.conf)
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server web:5000;
    }

    server {
        listen 80;
        server_name prazdnikvdom.kz www.prazdnikvdom.kz;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name prazdnikvdom.kz www.prazdnikvdom.kz;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
        }
    }
}

# Makefile для удобства разработки
.PHONY: install run migrate seed test clean docker-build docker-run

install:
	pip install -r requirements.txt

run:
	python run.py

migrate:
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

seed:
	python -c "from seed_data import seed_database; seed_database()"

test:
	python -m pytest tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

docker-build:
	docker build -t korolevstvo-chudes-api .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Скрипт для быстрого запуска (start.sh)
#!/bin/bash

echo "🎭 Запуск Королевство Чудес API..."

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

# Создаем базу данных если её нет
if [ ! -f "korolevstvo_chudes.db" ]; then
    echo "🗄️ Создание базы данных..."
    python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
    
    echo "🌱 Заполнение тестовыми данными..."
    python -c "from seed_data import seed_database; seed_database()"
fi

echo "🚀 Запуск сервера..."
python run.py