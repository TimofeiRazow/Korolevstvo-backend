from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
from models import db, Admin, BlogPost, Settings, Animator
from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import HTTPException
import click  # Добавить для CLI команд

# Инициализация расширений
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.url_map.strict_slashes = False
    CORS(app, supports_credentials=True, allowed_origins=app.config['CORS_ORIGINS'])
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Регистрация blueprints
    from routes.auth import auth_bp
    from routes.services import services_bp
    from routes.settings import settings_bp
    from routes.bookings import bookings_bp
    from routes.reviews import reviews_bp
    from routes.portfolio import portfolio_bp
    from routes.team import team_bp
    from routes.contact import contact_bp
    from routes.admin import admin_bp
    from routes.analytics import analytics_bp
    from routes.blog import blog_bp  # Убедитесь что импорт есть
    from routes.company_data import company_data_bp  # Импорт для company_data
    from routes.warehouse import warehouse_bp
    from routes.leads import leads_bp
    from routes.upload import upload_bp
    from routes.animators import animators_bp
    # from routes.bot_messages import telegram_bp
    # from routes.telegram_users import telegram_users_bp
    
    app.register_blueprint(leads_bp, url_prefix='/api/leads')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(warehouse_bp, url_prefix='/api/warehouse')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(blog_bp, url_prefix='/api/blog')
    app.register_blueprint(services_bp, url_prefix='/api/services')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(team_bp, url_prefix='/api/team')
    app.register_blueprint(contact_bp, url_prefix='/api/contact')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(company_data_bp, url_prefix='/api/company_data')
    app.register_blueprint(animators_bp, url_prefix='/api/animators')
    
    # Главная страница API
    @app.route('/api')
    def api_info():
        return jsonify({
            'message': 'Королевство Чудес API',
            'version': '1.0.0',
            'endpoints': {
                'services': '/api/services',
                'bookings': '/api/bookings',
                'reviews': '/api/reviews',
                'portfolio': '/api/portfolio',
                'team': '/api/team',
                'contact': '/api/contact',
                'admin': '/api/admin',
                'analytics': '/api/analytics',
                'telegram': '/api/telegram'
            },
            'telegram_bot': '@korolevstvo_chudes_bot'
        })

    return app

# ДОБАВИТЬ: Утилитные функции для блога
def get_client_ip(request):
    """Получение IP адреса клиента"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def paginate_query(query, page=1, per_page=20):
    """Утилита для пагинации запросов"""
    try:
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': pagination.items,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    except Exception as e:
        print(f"Ошибка пагинации: {e}")
        return {
            'items': [],
            'pagination': {
                'page': 1,
                'pages': 1,
                'per_page': per_page,
                'total': 0,
                'has_next': False,
                'has_prev': False
            }
        }

# ОБНОВИТЬ: Функция создания тестовых данных
def seed_admins():
    """Создание тестовых администраторов"""
    if Admin.query.count() > 0:
        return
    
    # Обычный администратор
    admin = Admin(
        name='Елена Петрова',
        email='manager@prazdnikvdom.kz',
        role='admin'
    )
    admin.set_password('manager123')
    db.session.add(admin)
    
    try:
        db.session.commit()
        print("Тестовые администраторы созданы:")
        print("- manager@prazdnikvdom.kz / manager123 (админ)")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании админов: {e}")

# ДОБАВИТЬ: Функция создания примеров статей блога
def seed_blog_posts():
    """Создание примеров статей блога"""
    try:
        # Проверяем есть ли статьи
        if BlogPost.query.count() > 0:
            print("Статьи блога уже существуют")
            return
        
        # Проверяем есть ли администратор
        admin = Admin.query.first()
        if not admin:
            print("Сначала создайте администратора")
            return
        
        # Создаем примеры статей
        sample_posts = [
            {
                'title': 'Как выбрать аниматора для детского праздника',
                'category': 'советы',
                'content': '''
                <h2>Основные критерии выбора аниматора</h2>
                <p>Выбор аниматора для детского праздника - ответственная задача. От этого зависит настроение детей и успех всего мероприятия.</p>
                
                <h3>На что обратить внимание:</h3>
                <ul>
                    <li><strong>Опыт работы с детьми</strong> - минимум 2 года практики</li>
                    <li><strong>Разнообразие программ</strong> - адаптация под возраст детей</li>
                    <li><strong>Качество костюмов</strong> - яркие, чистые, безопасные</li>
                    <li><strong>Отзывы родителей</strong> - реальные рекомендации</li>
                    <li><strong>Гибкость программы</strong> - возможность корректировки</li>
                </ul>
                
                <h3>Вопросы, которые стоит задать:</h3>
                <ol>
                    <li>Сколько детей одновременно может развлекать аниматор?</li>
                    <li>Какие игры подходят для данного возраста?</li>
                    <li>Есть ли запасной план на случай плохой погоды?</li>
                    <li>Включены ли реквизит и музыка в стоимость?</li>
                </ol>
                
                <p><em>Помните: хороший аниматор не только развлекает детей, но и учитывает их индивидуальные особенности, создавая атмосферу радости и безопасности.</em></p>
                ''',
                'excerpt': 'Полное руководство по выбору профессионального аниматора для незабываемого детского праздника. Критерии выбора, важные вопросы и советы от экспертов.',
                'tags': ['аниматоры', 'дети', 'праздники', 'советы'],
                'status': 'published',
                'featured': True,
                'author_id': admin.id,
                'author_name': admin.name,
                'meta_title': 'Как выбрать аниматора для детского праздника | Королевство Чудес',
                'meta_description': 'Советы по выбору аниматора для детского праздника. Критерии отбора, важные вопросы и рекомендации от профессионалов.'
            },
            {
                'title': 'Тренды детских праздников 2025',
                'category': 'тренды',
                'content': '''
                <h2>Актуальные направления в организации детских праздников</h2>
                <p>2025 год приносит новые тренды в мир детских праздников. Родители все больше ценят осмысленность и пользу развлечений.</p>
                
                <h3>Топ-5 трендов 2025 года:</h3>
                
                <h4>1. Экологические праздники</h4>
                <p>Дети учатся заботиться о природе через игры с переработанными материалами, создают поделки из натуральных компонентов.</p>
                
                <h4>2. STEM-вечеринки</h4>
                <p>Научные эксперименты становятся главным развлечением. Дети проводят безопасные опыты и изучают мир через практику.</p>
                
                <h4>3. Кулинарные мастер-классы</h4>
                <p>Готовка как развлечение набирает популярность. Дети учатся готовить простые блюда под руководством профессионалов.</p>
                
                <h4>4. Интерактивные квесты</h4>
                <p>Современные технологии делают квесты более захватывающими с использованием QR-кодов и мобильных приложений.</p>
                
                <h4>5. Mindfulness для детей</h4>
                <p>Элементы медитации и осознанности интегрируются в праздничные программы для развития эмоционального интеллекта.</p>
                
                <blockquote>
                <p>"Современные родители выбирают праздники, которые не только развлекают, но и развивают их детей" - тренд 2025 года.</p>
                </blockquote>
                ''',
                'excerpt': 'Узнайте о самых актуальных трендах в организации детских праздников на 2025 год. От эко-вечеринок до STEM-развлечений.',
                'tags': ['тренды', 'дети', '2025', 'праздники', 'развитие'],
                'status': 'published',
                'featured': True,
                'author_id': admin.id,
                'author_name': admin.name,
                'meta_title': 'Тренды детских праздников 2025 | Современные идеи',
                'meta_description': 'Актуальные тренды детских праздников 2025: эко-вечеринки, STEM-развлечения, кулинарные мастер-классы и интерактивные квесты.'
            },
            {
                'title': 'Организация свадьбы: чек-лист на 6 месяцев',
                'category': 'кейсы',
                'content': '''
                <h2>Пошаговый план подготовки к свадьбе</h2>
                <p>Подготовка к свадьбе может показаться сложной задачей. Наш детальный чек-лист поможет ничего не забыть.</p>
                
                <h3>За 6 месяцев до свадьбы:</h3>
                <ul>
                    <li>Определить бюджет и количество гостей</li>
                    <li>Выбрать и забронировать место проведения</li>
                    <li>Найти и забронировать фотографа</li>
                    <li>Определиться с концепцией и стилем</li>
                </ul>
                
                <h3>За 3 месяца:</h3>
                <ul>
                    <li>Заказать приглашения</li>
                    <li>Выбрать наряды</li>
                    <li>Организовать кейтеринг</li>
                    <li>Забронировать транспорт</li>
                </ul>
                
                <h3>За 1 месяц:</h3>
                <ul>
                    <li>Подтвердить все бронирования</li>
                    <li>Провести репетицию</li>
                    <li>Подготовить аварийный план</li>
                </ul>
                
                <div style="background: #f8f9fa; padding: 20px; border-left: 4px solid #6366f1; margin: 20px 0;">
                <h4>💡 Совет эксперта:</h4>
                <p>Начинайте планирование минимум за полгода. Это даст время для спокойного выбора поставщиков и избежания стресса.</p>
                </div>
                ''',
                'excerpt': 'Подробный чек-лист для организации свадьбы за 6 месяцев. Пошаговый план, который поможет ничего не забыть.',
                'tags': ['свадьба', 'планирование', 'чек-лист', 'организация'],
                'status': 'published',
                'featured': False,
                'author_id': admin.id,
                'author_name': admin.name,
                'meta_title': 'Чек-лист организации свадьбы за 6 месяцев | План подготовки',
                'meta_description': 'Полный чек-лист для организации свадьбы. Пошаговый план подготовки за 6 месяцев с важными этапами и сроками.'
            }
        ]
        
        for post_data in sample_posts:
            post = BlogPost(**post_data)
            db.session.add(post)
        
        db.session.commit()
        print(f"✅ Создано {len(sample_posts)} примеров статей блога")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при создании статей блога: {e}")

app = create_app()

# Существующие обработчики ошибок
@app.errorhandler(422)
def handle_unprocessable_entity(err):
    return jsonify({'error': '422', 'message': str(err)}), 422

@app.errorhandler(JWTExtendedException)
def handle_jwt_error(e):
    return jsonify({'error': 'JWT Error', 'message': str(e)}), 401

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify({'error': e.code, 'message': e.description}), e.code

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {'error': 'Токен истек'}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {'error': 'Недействительный токен'}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {'error': 'Требуется авторизация'}, 401

# Тестовый endpoint для проверки JWT
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return {'message': 'API работает', 'status': 'ok'}

# ДОБАВИТЬ: CLI команды для управления блогом
@app.cli.command()
def init_blog():
    """Инициализация блога с примерами статей"""
    print("🚀 Инициализация блога...")
    seed_blog_posts()

@app.cli.command()
@click.argument('slug')
def delete_post(slug):
    """Удалить статью по slug"""
    try:
        post = BlogPost.query.filter(BlogPost.slug == slug).first()
        if post:
            title = post.title
            db.session.delete(post)
            db.session.commit()
            print(f"✅ Статья '{title}' удалена")
        else:
            print(f"❌ Статья с slug '{slug}' не найдена")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при удалении статьи: {e}")

@app.cli.command()
def blog_stats():
    """Показать статистику блога"""
    try:
        total = BlogPost.query.count()
        published = BlogPost.query.filter(BlogPost.status == 'published').count()
        draft = BlogPost.query.filter(BlogPost.status == 'draft').count()
        featured = BlogPost.query.filter(BlogPost.featured == True).count()
        
        print("📊 Статистика блога:")
        print(f"   Всего статей: {total}")
        print(f"   Опубликовано: {published}")
        print(f"   Черновиков: {draft}")
        print(f"   Избранных: {featured}")
        
        # Статистика по категориям
        from sqlalchemy import func
        categories = db.session.query(
            BlogPost.category,
            func.count(BlogPost.id).label('count')
        ).group_by(BlogPost.category).all()
        
        if categories:
            print("\n📂 По категориям:")
            for category, count in categories:
                print(f"   {category}: {count}")
                
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")

# Добавить CLI команду для инициализации склада
@app.cli.command()
def init_warehouse():
    """Инициализация склада с примерами данных"""
    print("🏭 Инициализация склада...")
    from models import create_sample_warehouse_data
    create_sample_warehouse_data()


if __name__ == '__main__':    
    with app.app_context():
        db.create_all()
        seed_admins()
        seed_blog_posts()
        Settings.init_default_settings()
        # Добавляем инициализацию склада
        from models import create_sample_warehouse_data, create_sample_leads_data
        create_sample_warehouse_data()
        create_sample_leads_data()
    app.run(debug=True, host="0.0.0.0", port=5000)