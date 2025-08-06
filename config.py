import os
from datetime import timedelta

class Config:
    # Основные настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///korolevstvo_chudes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT настройки
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Email настройки
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@prazdnikvdom.kz'
    
    # Контактная информация
    COMPANY_INFO = {
        'name': 'Королевство Чудес',
        'phone': '+7 (7152) 123-456',
        'whatsapp': '+7 777 123 45 67',
        'email': 'info@prazdnikvdom.kz',
        'address': 'г. Петропавловск, ул. Конституции, 15, офис 201',
        'working_hours': 'Ежедневно с 9:00 до 21:00',
        'instagram': '@korolevstvo_chudes_pk',
        'website': 'prazdnikvdom.kz'
    }
    
    # Настройки загрузки файлов
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB максимум
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
    
    # API настройки
    ITEMS_PER_PAGE = 20
    MAX_PAGE_SIZE = 100