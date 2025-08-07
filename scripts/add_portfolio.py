import os
import sys
from datetime import datetime

# Добавляем корневую директорию проекта (на уровень выше scripts/) в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Portfolio
from app import create_app  # импортируем фабрику приложения

app = create_app()

# Данные для вставки
portfolio_data = [
    {
        'title': 'День рождения принцессы Амелии (5 лет)',
        'category': 'children',
        'date': datetime.strptime('2024-07-15', '%Y-%m-%d').date(),
        'location': 'Ресторан "Золотой дракон"',
        'guests': '25 детей',
        'rating': 5,
        'budget': '120,000 ₸',
        'description': 'Волшебный праздник в стиле Disney с аниматорами в костюмах принцесс, интерактивными играми и сказочным декором.',
        'tags': ['принцессы', 'disney', 'аниматоры', 'фотозона'],
        'images': [
            'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1464207687429-7505649dae38?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1607343833574-da7843101542?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
        ],
        'cover_image': 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'featured': True
    },
    {
        'title': 'Свадьба Алексея и Марии',
        'category': 'wedding',
        'date': datetime.strptime('2024-06-20', '%Y-%m-%d').date(),
        'location': 'Загородный комплекс "Весна"',
        'guests': '150 гостей',
        'rating': 5,
        'budget': '850,000 ₸',
        'description': 'Романтическая свадьба в стиле прованс с выездной регистрацией, живой музыкой и изысканным декором.',
        'tags': ['прованс', 'выездная регистрация', 'живая музыка', 'флористика'],
        'images': [
            'https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1465495976277-4387d4b0e4a6?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1606216794074-735e91aa2c92?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
        ],
        'cover_image': 'https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'featured': True
    },
    {
        'title': 'Корпоратив компании "ТехноПрогресс"',
        'category': 'corporate',
        'date': datetime.strptime('2024-05-18', '%Y-%m-%d').date(),
        'location': 'Конференц-зал "Метрополь"',
        'guests': '80 сотрудников',
        'rating': 5,
        'budget': '450,000 ₸',
        'description': 'Новогодний корпоратив в стиле "Голливуд" с красной дорожкой, шоу-программой и тимбилдинг активностями.',
        'tags': ['голливуд', 'тимбилдинг', 'шоу-программа', 'красная дорожка'],
        'images': [
            'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1556742393-d75f468bfcb0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
        ],
        'cover_image': 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'featured': False
    },
    {
        'title': 'Юбилей 60 лет Валентины Николаевны',
        'category': 'anniversary',
        'date': datetime.strptime('2024-04-12', '%Y-%m-%d').date(),
        'location': 'Ресторан "Империя"',
        'guests': '45 гостей',
        'rating': 5,
        'budget': '280,000 ₸',
        'description': 'Элегантный юбилей с живой музыкой, поздравлениями от звезд и трогательными видео от родных.',
        'tags': ['юбилей', 'живая музыка', 'поздравления', 'элегантность'],
        'images': [
            'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1551963831-b3b1ca40c98e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
        ],
        'cover_image': 'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'featured': False
    },
    {
        'title': 'Огненное шоу на открытии ресторана',
        'category': 'show',
        'date': datetime.strptime('2024-03-25', '%Y-%m-%d').date(),
        'location': 'Ресторан "Fire Palace"',
        'guests': '200 гостей',
        'rating': 5,
        'budget': '320,000 ₸',
        'description': 'Захватывающее огненное шоу с акробатическими элементами и пиротехникой для торжественного открытия.',
        'tags': ['огненное шоу', 'акробатика', 'пиротехника', 'открытие'],
        'images': [
            'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
        ],
        'cover_image': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'featured': False
    },
    {
        'title': 'Квест "Пираты Карибского моря" (10-12 лет)',
        'category': 'children',
        'date': datetime.strptime('2024-02-14', '%Y-%m-%d').date(),
        'location': 'Квест-центр "Приключения"',
        'guests': '15 детей',
        'rating': 5,
        'budget': '95,000 ₸',
        'description': 'Интерактивный квест с поиском сокровищ, костюмированными персонажами и морскими приключениями.',
        'tags': ['квест', 'пираты', 'приключения', 'интерактив'],
        'images': [
            'https://images.unsplash.com/photo-1606041008023-472dfb5e530f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
        ],
        'cover_image': 'https://images.unsplash.com/photo-1606041008023-472dfb5e530f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'featured': False
    }
]


def populate_portfolio():
    try:
        with app.app_context():
            # Portfolio.query.delete()  # если нужно очистить

            for item in portfolio_data:
                portfolio = Portfolio(
                    title=item['title'],
                    category=item['category'],
                    date=item['date'],
                    location=item['location'],
                    guests=item['guests'],
                    rating=item['rating'],
                    budget=item['budget'],
                    description=item['description'],
                    tags=item['tags'],
                    images=item['images'],
                    cover_image=item['cover_image'],
                    featured=item['featured']
                )
                db.session.add(portfolio)

            db.session.commit()
            print(f"Успешно добавлено {len(portfolio_data)} записей в базу данных!")

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при добавлении данных: {e}")

# Запускаем функцию и выводим результат
with app.app_context():
    populate_portfolio()

    portfolio_count = Portfolio.query.count()
    print(f"Общее количество записей в портфолио: {portfolio_count}")

    all_portfolio = Portfolio.query.all()
    for item in all_portfolio:
        print(f"ID: {item.id}, Заголовок: {item.title}, Категория: {item.category}")
