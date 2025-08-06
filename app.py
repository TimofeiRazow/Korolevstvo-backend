from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

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