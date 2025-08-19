# config.py - обновленная конфигурация с настройками Telegram
import os
from datetime import timedelta

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Настройки базы данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///korolevstvo_chudes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Настройки JWT для админки
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Email настройки
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'info@prazdnikvdom.kz'
    
    # Настройки Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or '8372397030:AAG5bjF0b2WufVVoSsqelAdBpV6LVm1raJE'
    TELEGRAM_WEBHOOK_URL = os.environ.get('TELEGRAM_WEBHOOK_URL')  # https://yourdomain.com/api/telegram/webhook
    TELEGRAM_ADMIN_CHAT_ID = os.environ.get('TELEGRAM_ADMIN_CHAT_ID') or '5032645933'
    
    # Настройки файлов
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Настройки безопасности
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Настройки пагинации
    POSTS_PER_PAGE = 20
    BOOKINGS_PER_PAGE = 50
    REVIEWS_PER_PAGE = 30
    
    # Настройки кеширования
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Настройки логирования
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'
    
    # API настройки
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT') or '100/hour'
    
    # Настройки уведомлений
    NOTIFICATION_SETTINGS = {
        'email_enabled': True,
        'telegram_enabled': True,
        'sms_enabled': False,  # Пока не реализовано
        'webhook_enabled': False  # Для интеграции с внешними системами
    }
    
    # Настройки бизнес-логики
    BUSINESS_SETTINGS = {
        'company_name': 'Королевство Чудес',
        'company_phone': '+7 (XXX) XXX-XX-XX',
        'company_email': 'info@prazdnikvdom.kz',
        'company_address': 'г. Петропавловск, ул. Примерная, 123',
        'working_hours': 'Пн-Пт: 9:00-18:00, Сб-Вс: 10:00-16:00',
        'timezone': 'Asia/Almaty',
        'currency': '₸',
        'min_booking_advance_days': 3,  # Минимальное количество дней для бронирования
        'max_booking_advance_days': 365,  # Максимальное количество дней для бронирования
    }
    
    # Настройки социальных сетей
    SOCIAL_MEDIA = {
        'instagram': 'https://instagram.com/korolevstvo_chudes',
        'vk': 'https://vk.com/korolevstvo_chudes',
        'telegram': 'https://t.me/korolevstvo_chudes_bot',
        'whatsapp': '+77051234567',
        'youtube': 'https://youtube.com/@korolevstvo_chudes'
    }
    
    # Настройки SEO
    SEO_SETTINGS = {
        'site_name': 'Королевство Чудес - Праздничное агентство',
        'site_description': 'Организация незабываемых праздников в Петропавловске. Детские дни рождения, свадьбы, корпоративы. Более 1000 счастливых клиентов!',
        'site_keywords': 'праздники, аниматоры, свадьбы, дети рождения, корпоративы, Петропавловск',
        'site_url': 'https://prazdnikvdom.kz',
        'robots_txt': 'User-agent: *\nAllow: /',
        'sitemap_enabled': True
    }

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
    TELEGRAM_WEBHOOK_URL = None  # В разработке webhook не используется
    
class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    TELEGRAM_BOT_TOKEN = 'test-token'
    
class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/db'
    
    # В продакшене обязательно нужны эти переменные окружения
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Логирование в файл
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                Config.LOG_FILE, 
                maxBytes=10240, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Королевство Чудес startup')

# Выбор конфигурации по переменной окружения
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Получить текущую конфигурацию"""
    return config[os.environ.get('FLASK_ENV') or 'default']

# Валидация критически важных настроек
def validate_config():
    """Проверить корректность конфигурации"""
    errors = []
    
    if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key-change-in-production':
        if os.environ.get('FLASK_ENV') == 'production':
            errors.append("SECRET_KEY должен быть установлен в продакшене")
    
    if not Config.TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN обязателен для работы бота")
    
    if os.environ.get('FLASK_ENV') == 'production':
        if not Config.TELEGRAM_WEBHOOK_URL:
            errors.append("TELEGRAM_WEBHOOK_URL обязателен в продакшене")
        
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            errors.append("Email настройки обязательны в продакшене")
    
    if errors:
        print("❌ Ошибки конфигурации:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    print("✅ Конфигурация корректна")
    return True

# Утилита для создания .env файла
def create_env_template():
    """Создать шаблон .env файла"""
    env_template = """# Flask настройки
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# База данных
DATABASE_URL=sqlite:///korolevstvo_chudes.db

# Email настройки
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=info@prazdnikvdom.kz

# Telegram настройки
TELEGRAM_BOT_TOKEN=8372397030:AAG5bjF0b2WufVVoSsqelAdBpV6LVm1raJE
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/telegram/webhook
TELEGRAM_ADMIN_CHAT_ID=5032645933

# Файлы
UPLOAD_FOLDER=uploads

# Логирование
LOG_LEVEL=INFO
LOG_FILE=app.log

# API
API_RATE_LIMIT=100/hour

# Кеширование
CACHE_TYPE=simple
"""
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    print("✅ Создан файл .env.template")
    print("Скопируйте его в .env и заполните своими значениями")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate_config()
    elif len(sys.argv) > 1 and sys.argv[1] == "create-env":
        create_env_template()
    else:
        print("Использование:")
        print("  python config.py validate     - Проверить конфигурацию")
        print("  python config.py create-env   - Создать шаблон .env файла")