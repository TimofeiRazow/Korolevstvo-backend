from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
from models import db, Admin
from flask_jwt_extended.exceptions import JWTExtendedException
from flask import jsonify
from werkzeug.exceptions import HTTPException

# Инициализация расширений
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    
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
    
    # Главная страница API
    @app.route('/api/')
    def index():
        return {
            'message': 'Королевство Чудес API',
            'version': '1.0.0',
            'status': 'active'
        }
    
    return app

# Пока что не работает
def seed_admins():
    
    from models import Admin
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


app = create_app()


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

if __name__ == '__main__':    

    with app.app_context():
        db.create_all()
        seed_admins()  # безопасный вызов
    app.run(debug=True)

