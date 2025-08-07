from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
from models import Admin

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    
    # Регистрация blueprints
    from routes.auth import auth_bp
    from routes.services import services_bp
    from routes.bookings import bookings_bp
    from routes.reviews import reviews_bp
    from routes.portfolio import portfolio_bp
    from routes.team import team_bp
    from routes.contact import contact_bp
    from routes.admin import admin_bp
    from routes.analytics import analytics_bp
    
    app.register_blueprint(services_bp, url_prefix='/api/services')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(team_bp, url_prefix='/api/team')
    app.register_blueprint(contact_bp, url_prefix='/api/contact')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    @app.before_first_request
    def create_super_admin():
        if not Admin.query.filter_by(role='super_admin').first():
            super_admin = Admin(
                name='Супер Администратор',
                email='admin@prazdnikvdom.kz',
                role='super_admin'
            )
            super_admin.set_password('admin123')  # Изменить в продакшене!
            
            db.session.add(super_admin)
            db.session.commit()
            print("Создан суперадминистратор: admin@prazdnikvdom.kz / admin123")
    # Главная страница API
    @app.route('/api/')
    def index():
        return {
            'message': 'Королевство Чудес API',
            'version': '1.0.0',
            'status': 'active'
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

# Пока что не работает
def seed_admins():
    """Создание тестовых администраторов"""
    if Admin.query.count() > 0:
        return
    
    # Супер-администратор
    super_admin = Admin(
        name='Ольга Иванова',
        email='admin@prazdnikvdom.kz',
        role='super_admin'
    )
    super_admin.set_password('admin123')
    db.session.add(super_admin)
    
    # Обычный администратор
    admin = Admin(
        name='Елена Петрова',
        email='manager@prazdnikvdom.kz',
        role='admin'
    )
    admin.set_password('manager123')
    db.session.add(admin)
    
    # Менеджер
    manager = Admin(
        name='Анна Сидорова',
        email='editor@prazdnikvdom.kz',
        role='manager'
    )
    manager.set_password('editor123')
    db.session.add(manager)
    
    try:
        db.session.commit()
        print("Тестовые администраторы созданы:")
        print("- admin@prazdnikvdom.kz / admin123 (супер-админ)")
        print("- manager@prazdnikvdom.kz / manager123 (админ)")
        print("- editor@prazdnikvdom.kz / editor123 (менеджер)")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании админов: {e}")