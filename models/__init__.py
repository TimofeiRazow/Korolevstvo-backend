# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='admin')  # admin, manager, editor
    active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    
    def set_password(self, password):
        """Хешировать пароль"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверить пароль"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Обновить время последнего входа"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
# models/service.py
class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50))
    min_guests = db.Column(db.String(50))
    rating = db.Column(db.Float, default=5.0)
    price = db.Column(db.String(50))
    price_description = db.Column(db.String(100))
    description = db.Column(db.Text)
    features = db.Column(db.JSON)  # Список особенностей
    subcategories = db.Column(db.JSON)  # Подкатегории
    images = db.Column(db.JSON)  # Список изображений
    cover_image = db.Column(db.String(500))
    featured = db.Column(db.Boolean, default=False)
    tags = db.Column(db.JSON)  # Теги для поиска
    packages = db.Column(db.JSON)  # Пакеты услуг
    status = db.Column(db.String(20), default='active')  # active, inactive, draft
    views_count = db.Column(db.Integer, default=0)  # Счетчик просмотров
    bookings_count = db.Column(db.Integer, default=0)  # Счетчик бронирований
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'duration': self.duration,
            'minGuests': self.min_guests,
            'rating': self.rating,
            'price': self.price,
            'priceDescription': self.price_description,
            'description': self.description,
            'features': self.features or [],
            'subcategories': self.subcategories or [],
            'images': self.images or [],
            'coverImage': self.cover_image,
            'featured': self.featured,
            'tags': self.tags or [],
            'packages': self.packages or [],
            'status': self.status,
            'viewsCount': self.views_count,
            'bookingsCount': self.bookings_count,
            'created': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
            'updated': self.updated_at.strftime('%Y-%m-%d') if self.updated_at else None
        }
    
    def update_from_dict(self, data):
        """Обновление модели из словаря данных"""
        self.title = data.get('title', self.title)
        self.category = data.get('category', self.category)
        self.duration = data.get('duration', self.duration)
        self.min_guests = data.get('minGuests', self.min_guests)
        self.rating = float(data.get('rating', self.rating))
        self.price = data.get('price', self.price)
        self.price_description = data.get('priceDescription', self.price_description)
        self.description = data.get('description', self.description)
        self.cover_image = data.get('coverImage', self.cover_image)
        self.featured = bool(data.get('featured', self.featured))
        self.status = data.get('status', self.status)
        
        # Обработка списковых полей
        if 'features' in data:
            if isinstance(data['features'], str):
                self.features = [f.strip() for f in data['features'].split(',') if f.strip()]
            else:
                self.features = data['features']
                
        if 'subcategories' in data:
            if isinstance(data['subcategories'], str):
                self.subcategories = [s.strip() for s in data['subcategories'].split(',') if s.strip()]
            else:
                self.subcategories = data['subcategories']
                
        if 'tags' in data:
            if isinstance(data['tags'], str):
                self.tags = [t.strip() for t in data['tags'].split(',') if t.strip()]
            else:
                self.tags = data['tags']
                
        if 'images' in data:
            if isinstance(data['images'], str):
                self.images = [i.strip() for i in data['images'].split(',') if i.strip()]
            else:
                self.images = data['images']
        
        self.updated_at = datetime.utcnow()

# models/booking.py
class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    service_title = db.Column(db.String(100))
    event_date = db.Column(db.Date)
    event_time = db.Column(db.Time)
    guests_count = db.Column(db.Integer)
    budget = db.Column(db.String(50))
    location = db.Column(db.String(200))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='new')  # new, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    service = db.relationship('Service', backref='bookings')
    
    def to_dict(self):
        try:
            return {
                'id': self.id,
                'name': self.name,
                'phone': self.phone,
                'email': self.email,
                'service_id': self.service_id,
                'service_title': self.service_title if self.service_title else None,
                'event_date': self.event_date.isoformat() if self.event_date else None,
                'event_time': self.event_time.isoformat() if self.event_time else None,
                'guests_count': self.guests_count,
                'budget': self.budget,
                'location': self.location,
                'message': self.message,
                'status': self.status,
                'created_at': self.created_at.isoformat()
            }
        except Exception as e:
            print("Ошибка в to_dict:", e)
            return {'error': str(e)}

# models/review.py
class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    service_type = db.Column(db.String(100), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.String(10), default='👤')
    approved = db.Column(db.Boolean, default=False, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)  # Избранный отзыв
    helpful_count = db.Column(db.Integer, default=0)  # Количество "полезно"
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    service = db.relationship('Service', backref='reviews', lazy=True)
    
    def __init__(self, **kwargs):
        super(Review, self).__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_personal_info=False):
        """Преобразование в словарь с возможностью скрытия персональных данных"""
        data = {
            'id': self.id,
            'name': self.name,
            'service_type': self.service_type,
            'service_id': self.service_id,
            'rating': self.rating,
            'text': self.text,
            'avatar': self.avatar,
            'approved': self.approved,
            'featured': self.featured,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'date': self.created_at.isoformat() if self.created_at else None  # Для обратной совместимости
        }
        
        # Добавляем персональную информацию только если запрошено (для админки)
        if include_personal_info:
            data.update({
                'email': self.email,
                'phone': self.phone
            })
        
        # Добавляем информацию об услуге, если есть связь
        if self.service:
            data['service'] = {
                'id': self.service.id,
                'name': self.service.name,
                'slug': getattr(self.service, 'slug', None)
            }
        
        return data

# ЕДИНАЯ МОДЕЛЬ ПОРТФОЛИО (объединяет все поля из React компонента)
# ОБНОВЛЕННАЯ МОДЕЛЬ ПОРТФОЛИО
class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    
    # Основные поля
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # children, wedding, corporate, anniversary, show
    date = db.Column(db.Date, nullable=False)  # Дата мероприятия
    description = db.Column(db.Text)
    budget = db.Column(db.String(50))  # Бюджет проекта (например: "250,000 ₸")
    client = db.Column(db.String(100))  # Имя клиента
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    
    # Дополнительные поля для соответствия React компонентам
    location = db.Column(db.String(200))  # Место проведения
    guests = db.Column(db.String(50))  # Количество гостей (например: "25 детей")
    rating = db.Column(db.Integer, default=5)  # Рейтинг проекта (1-5)
    tags = db.Column(db.JSON)  # Теги ['принцессы', 'disney', 'аниматоры']
    
    # Изображения
    images = db.Column(db.JSON)  # Список URL изображений
    cover_image = db.Column(db.String(500))  # URL обложки
    photos_count = db.Column(db.Integer, default=0)  # Количество фото
    
    # Пакеты услуг для бронирования
    packages = db.Column(db.JSON)  # [{"name": "Базовый", "price": "85,000 ₸", "features": [...]}, ...]
    
    # Статус и метрики
    featured = db.Column(db.Boolean, default=False)  # Избранный проект
    views = db.Column(db.Integer, default=0)  # Счетчик просмотров
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, for_admin=False):
        """Преобразование в словарь для API"""
        data = {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'budget': self.budget,
            'status': self.status,
            'location': self.location,
            'guests': self.guests,
            'rating': self.rating,
            'tags': self.tags or [],
            'images': self.images or [],
            'coverImage': self.cover_image,
            'photos': self.photos_count,
            'packages': self.packages or [],
            'featured': self.featured,
            'views': self.views,
            'created': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Для админки добавляем приватную информацию
        if for_admin:
            data.update({
                'client': self.client,
            })
        
        return data
    
    def increment_views(self, ip_address=None, user_agent=None):
        """Увеличить счетчик просмотров с проверкой дубликатов"""
        # Проверяем, не было ли просмотра с того же IP за последние 30 минут
        if ip_address:
            recent_view = PortfolioView.query.filter(
                PortfolioView.portfolio_id == self.id,
                PortfolioView.ip_address == ip_address,
                PortfolioView.viewed_at > (datetime.utcnow() - timedelta(minutes=30))
            ).first()
            
            if recent_view:
                return False  # Не засчитываем повторный просмотр
        
        # Записываем новый просмотр
        view = PortfolioView(
            portfolio_id=self.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(view)
        
        # Увеличиваем общий счетчик
        self.views = (self.views or 0) + 1
        db.session.commit()
        return True
    
    def update_photos_count(self):
        """Обновить количество фото на основе списка изображений"""
        if self.images:
            self.photos_count = len(self.images)
        else:
            self.photos_count = 0
        db.session.commit()
    
    @classmethod
    def get_by_status(cls, status='published'):
        """Получить проекты по статусу"""
        return cls.query.filter(cls.status == status).order_by(cls.date.desc()).all()
    
    @classmethod
    def get_by_category(cls, category, status='published'):
        """Получить проекты по категории"""
        query = cls.query.filter(cls.category == category)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.date.desc()).all()
    
    @classmethod
    def get_featured(cls, limit=6, status='published'):
        """Получить избранные проекты"""
        query = cls.query.filter(cls.featured == True)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.date.desc()).limit(limit).all()
    
    @classmethod
    def get_stats(cls):
        """Получить статистику портфолио"""
        total = cls.query.count()
        published = cls.query.filter(cls.status == 'published').count()
        draft = cls.query.filter(cls.status == 'draft').count()
        archived = cls.query.filter(cls.status == 'archived').count()
        
        # Топ категории
        categories = db.session.query(
            cls.category,
            func.count(cls.id).label('count')
        ).filter(cls.status == 'published').group_by(cls.category).all()
        
        return {
            'total': total,
            'published': published,
            'draft': draft,
            'archived': archived,
            'total_views': db.session.query(func.sum(cls.views)).scalar() or 0,
            'categories': [{'name': cat, 'count': count} for cat, count in categories]
        }


class PortfolioView(db.Model):
    """Модель для детального отслеживания просмотров портфолио"""
    __tablename__ = 'portfolio_views'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    ip_address = db.Column(db.String(45))  # Поддержка IPv6
    user_agent = db.Column(db.String(500))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    portfolio = db.relationship('Portfolio', backref='view_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500))
    description = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    specialization = db.Column(db.JSON)  # Специализации
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'image': self.image,
            'description': self.description,
            'phone': self.phone,
            'email': self.email,
            'specialization': self.specialization,
            'active': self.active
        }

# models/settings.py
class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string')  # string, boolean, json, number
    category = db.Column(db.String(50))  # company, social, notifications, seo, integration
    description = db.Column(db.String(255))  # Описание настройки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings_dict(cls, category=None):
        """Получить настройки в виде словаря"""
        query = cls.query
        if category:
            query = query.filter(cls.category == category)
        
        settings = query.all()
        result = {}
        
        for setting in settings:
            # Преобразование значения в соответствии с типом
            if setting.value_type == 'boolean':
                result[setting.key] = setting.value.lower() in ('true', '1', 'yes')
            elif setting.value_type == 'number':
                try:
                    result[setting.key] = float(setting.value) if '.' in setting.value else int(setting.value)
                except:
                    result[setting.key] = setting.value
            elif setting.value_type == 'json':
                try:
                    import json
                    result[setting.key] = json.loads(setting.value)
                except:
                    result[setting.key] = {}
            else:
                result[setting.key] = setting.value
        
        return result
    
    @classmethod
    def update_setting(cls, key, value, value_type='string', category=None, description=None):
        """Обновить или создать настройку"""
        setting = cls.query.filter(cls.key == key).first()
        
        if setting:
            setting.value = str(value) if value is not None else None
            setting.value_type = value_type
            setting.updated_at = datetime.utcnow()
        else:
            setting = cls(
                key=key,
                value=str(value) if value is not None else None,
                value_type=value_type,
                category=category,
                description=description
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Получить одну настройку"""
        setting = cls.query.filter(cls.key == key).first()
        if not setting:
            return default
        
        if setting.value_type == 'boolean':
            return setting.value.lower() in ('true', '1', 'yes')
        elif setting.value_type == 'number':
            try:
                return float(setting.value) if '.' in setting.value else int(setting.value)
            except:
                return setting.value
        elif setting.value_type == 'json':
            try:
                import json
                return json.loads(setting.value)
            except:
                return {}
        else:
            return setting.value
    
    @classmethod
    def init_default_settings(cls):
        """Инициализация настроек по умолчанию"""
        defaults = [
            # Компания
            ('company_name', 'Королевство Чудес', 'string', 'company', 'Название компании'),
            ('company_email', 'info@prazdnikvdom.kz', 'string', 'company', 'Email компании'),
            ('company_phone', '+7 (777) 123-45-67', 'string', 'company', 'Основной телефон'),
            ('whatsapp_phone', '+7 (777) 987-65-43', 'string', 'company', 'WhatsApp номер'),
            ('company_address', 'г. Петропавловск, ул. Ленина, 123', 'string', 'company', 'Адрес компании'),
            ('company_description', 'Профессиональная организация праздников и мероприятий', 'string', 'company', 'Описание компании'),
            
            # Социальные сети
            ('social_instagram', 'https://instagram.com/korolevstvo_chudes', 'string', 'social', 'Instagram'),
            ('social_facebook', '', 'string', 'social', 'Facebook'),
            ('social_youtube', '', 'string', 'social', 'YouTube'),
            ('social_telegram', '', 'string', 'social', 'Telegram'),
            
            # Уведомления
            ('email_notifications', 'true', 'boolean', 'notifications', 'Email уведомления'),
            ('telegram_notifications', 'false', 'boolean', 'notifications', 'Telegram уведомления'),
            ('sms_notifications', 'false', 'boolean', 'notifications', 'SMS уведомления'),
            ('notification_email', 'admin@prazdnikvdom.kz', 'string', 'notifications', 'Email для уведомлений'),
            
            # SEO
            ('site_title', 'Организация праздников в Петропавловске - Королевство Чудес', 'string', 'seo', 'Заголовок сайта'),
            ('site_description', 'Профессиональная организация праздников в Петропавловске. Детские дни рождения, свадьбы, корпоративы.', 'string', 'seo', 'Описание сайта'),
            ('site_keywords', 'праздники петропавловск, аниматоры, организация свадеб', 'string', 'seo', 'Ключевые слова'),
            ('google_analytics_id', '', 'string', 'seo', 'Google Analytics ID'),
            ('yandex_metrica_id', '', 'string', 'seo', 'Яндекс.Метрика ID'),
            
            # Интеграции
            ('kaspi_api_key', '', 'string', 'integration', 'API ключ Kaspi'),
            ('one_c_url', '', 'string', 'integration', 'URL сервера 1C'),
            ('smtp_server', '', 'string', 'integration', 'SMTP сервер'),
            ('smtp_port', '', 'string', 'integration', 'SMTP порт'),
        ]
        
        for key, value, value_type, category, description in defaults:
            if not cls.query.filter(cls.key == key).first():
                setting = cls(
                    key=key,
                    value=value,
                    value_type=value_type,
                    category=category,
                    description=description
                )
                db.session.add(setting)
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'category': self.category,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    cover_image = db.Column(db.String(500))  # URL обложки
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    tags = db.Column(db.JSON)  # Список тегов
    status = db.Column(db.String(20), default='draft')  # draft, published, scheduled, archived
    featured = db.Column(db.Boolean, default=False)
    
    # SEO поля
    meta_title = db.Column(db.String(60))
    meta_description = db.Column(db.String(160))
    
    # Изображения
    featured_image = db.Column(db.String(500))  # URL главного изображения
    gallery = db.Column(db.JSON)  # Дополнительные изображения
    
    # Автор
    author_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)  # Публичное имя автора
    
    # Метрики
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    
    # Настройки публикации
    scheduled_date = db.Column(db.DateTime)  # Для отложенной публикации
    published_at = db.Column(db.DateTime)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    author = db.relationship('Admin', backref='blog_posts', lazy=True)
    
    def __init__(self, **kwargs):
        super(BlogPost, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
        if self.status == 'published' and not self.published_at:
            self.published_at = datetime.utcnow()
    
    @staticmethod
    def generate_slug(title):
        """Генерация slug из заголовка"""
        import re
        import unicodedata
        
        # Транслитерация русских букв
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        slug = title.lower()
        for ru, en in translit_dict.items():
            slug = slug.replace(ru, en)
        
        # Убираем все кроме букв, цифр и пробелов
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', slug)
        # Заменяем пробелы и множественные дефисы на один дефис
        slug = re.sub(r'[\s-]+', '-', slug)
        # Убираем дефисы в начале и конце
        slug = slug.strip('-')
        
        return slug
    
    @classmethod
    def get_stats(cls):
        """Получить статистику блога с поддержкой разных СУБД"""
        try:
            total = cls.query.count()
            published = cls.query.filter(cls.status == 'published').count()
            draft = cls.query.filter(cls.status == 'draft').count()
            scheduled = cls.query.filter(cls.status == 'scheduled').count()
            archived = cls.query.filter(cls.status == 'archived').count()
            featured = cls.query.filter(cls.featured == True, cls.status == 'published').count()
            
            # Топ категории
            categories = db.session.query(
                cls.category,
                func.count(cls.id).label('count')
            ).filter(cls.status == 'published').group_by(cls.category).all()
            
            # Общее количество просмотров
            total_views = db.session.query(func.sum(cls.views_count)).scalar() or 0
            
            # Среднее количество просмотров
            avg_views = db.session.query(func.avg(cls.views_count)).filter(
                cls.views_count.isnot(None),
                cls.status == 'published'
            ).scalar() or 0
            
            return {
                'total': total,
                'published': published,
                'draft': draft,
                'scheduled': scheduled,
                'archived': archived,
                'featured': featured,
                'total_views': int(total_views),
                'avg_views': round(float(avg_views), 1),
                'categories': [
                    {
                        'name': cat, 
                        'count': count,
                        'slug': cat.lower().replace(' ', '-') if cat else 'uncategorized'
                    } 
                    for cat, count in categories
                ]
            }
        except Exception as e:
            print(f"Error getting blog stats: {e}")
            return {
                'total': 0,
                'published': 0,
                'draft': 0,
                'scheduled': 0,
                'archived': 0,
                'featured': 0,
                'total_views': 0,
                'avg_views': 0,
                'categories': []
            }

    @classmethod
    def get_monthly_stats(cls, limit_months=12):
        """Получить статистику по месяцам с поддержкой SQLite и PostgreSQL"""
        try:
            # Определяем тип базы данных
            engine_name = db.engine.name
            
            if engine_name == 'postgresql':
                # Для PostgreSQL используем date_trunc
                monthly_query = db.session.query(
                    db.func.date_trunc('month', cls.created_at).label('month'),
                    db.func.count(cls.id).label('posts_count'),
                    db.func.sum(cls.views_count).label('total_views')
                ).group_by(
                    db.func.date_trunc('month', cls.created_at)
                ).order_by(
                    db.func.date_trunc('month', cls.created_at).desc()
                ).limit(limit_months)
            else:
                # Для SQLite используем strftime
                monthly_query = db.session.query(
                    db.func.strftime('%Y-%m', cls.created_at).label('month'),
                    db.func.count(cls.id).label('posts_count'),
                    db.func.sum(cls.views_count).label('total_views')
                ).group_by(
                    db.func.strftime('%Y-%m', cls.created_at)
                ).order_by(
                    db.func.strftime('%Y-%m', cls.created_at).desc()
                ).limit(limit_months)
            
            results = monthly_query.all()
            
            monthly_stats = []
            for month, posts_count, total_views in results:
                monthly_stats.append({
                    'month': str(month) if month else 'N/A',
                    'posts_count': posts_count or 0,
                    'total_views': int(total_views) if total_views else 0
                })
            
            return monthly_stats
            
        except Exception as e:
            print(f"Error getting monthly stats: {e}")
            return []

    @classmethod
    def get_top_posts(cls, limit=10, by_views=True):
        """Получить топ статей"""
        try:
            if by_views:
                query = cls.query.filter(
                    cls.status == 'published',
                    cls.views_count.isnot(None)
                ).order_by(cls.views_count.desc())
            else:
                query = cls.query.filter(
                    cls.status == 'published'
                ).order_by(cls.created_at.desc())
            
            posts = query.limit(limit).all()
            
            return [
                {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'category': post.category,
                    'views_count': post.views_count or 0,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'author_name': post.author_name
                } for post in posts
            ]
            
        except Exception as e:
            print(f"Error getting top posts: {e}")
            return []

    @classmethod
    def search_advanced(cls, query_text, category=None, status='published', limit=20):
        """Расширенный поиск статей"""
        try:
            search_filter = f"%{query_text}%"
            
            query = cls.query.filter(
                db.or_(
                    cls.title.ilike(search_filter),
                    cls.content.ilike(search_filter),
                    cls.excerpt.ilike(search_filter)
                )
            )
            
            if status:
                query = query.filter(cls.status == status)
            
            if category:
                query = query.filter(cls.category == category)
            
            posts = query.order_by(cls.published_at.desc()).limit(limit).all()
            
            return posts
            
        except Exception as e:
            print(f"Error in advanced search: {e}")
            return []
    
    def to_dict(self, include_content=True, for_admin=False):
        """Преобразование в словарь для API"""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'category': self.category,
            'cover_image': self.cover_image,
            'excerpt': self.excerpt,
            'tags': self.tags or [],
            'status': self.status,
            'featured': self.featured,
            'featured_image': self.featured_image,
            'gallery': self.gallery or [],
            'author_name': self.author_name,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'shares_count': self.shares_count,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'date': self.published_at.strftime('%Y-%m-%d') if self.published_at else self.created_at.strftime('%Y-%m-%d')
        }
        
        # Добавляем контент только если нужно (для списков статей может не понадобиться)
        if include_content:
            data['content'] = self.content
        
        # Для админки добавляем дополнительную информацию
        if for_admin:
            data.update({
                'author_id': self.author_id,
                'meta_title': self.meta_title,
                'meta_description': self.meta_description,
                'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            })
        
        return data
    
    def update_from_dict(self, data):
        """Обновление модели из словаря данных"""
        self.title = data.get('title', self.title)
        self.category = data.get('category', self.category)
        self.content = data.get('content', self.content)
        self.excerpt = data.get('excerpt', self.excerpt)
        self.status = data.get('status', self.status)
        self.featured = bool(data.get('featured', self.featured))
        self.featured_image = data.get('featured_image', self.featured_image)
        self.author_name = data.get('author_name', self.author_name)
        self.meta_title = data.get('meta_title', self.meta_title)
        self.meta_description = data.get('meta_description', self.meta_description)
        
        # Обработка slug
        if 'slug' in data and data['slug']:
            self.slug = data['slug']
        elif self.title:
            self.slug = self.generate_slug(self.title)
        
        # Обработка списковых полей
        if 'tags' in data:
            if isinstance(data['tags'], str):
                self.tags = [t.strip() for t in data['tags'].split(',') if t.strip()]
            else:
                self.tags = data['tags']
        
        if 'gallery' in data:
            if isinstance(data['gallery'], str):
                self.gallery = [g.strip() for g in data['gallery'].split(',') if g.strip()]
            else:
                self.gallery = data['gallery']
        
        # Обработка даты публикации
        if data.get('status') == 'published' and not self.published_at:
            self.published_at = datetime.utcnow()
        elif data.get('status') != 'published':
            self.published_at = None
        
        # Обработка отложенной публикации
        if 'scheduled_date' in data:
            if data['scheduled_date']:
                try:
                    self.scheduled_date = datetime.fromisoformat(data['scheduled_date'])
                except:
                    self.scheduled_date = None
            else:
                self.scheduled_date = None
        
        self.updated_at = datetime.utcnow()
    
    def increment_views(self, ip_address=None, user_agent=None):
        """Увеличить счетчик просмотров с проверкой дубликатов"""
        if ip_address:
            # Проверяем, не было ли просмотра с того же IP за последние 30 минут
            recent_view = BlogView.query.filter(
                BlogView.blog_post_id == self.id,
                BlogView.ip_address == ip_address,
                BlogView.viewed_at > (datetime.utcnow() - timedelta(minutes=30))
            ).first()
            
            if recent_view:
                return False  # Не засчитываем повторный просмотр
        
        # Записываем новый просмотр
        view = BlogView(
            blog_post_id=self.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(view)
        
        # Увеличиваем общий счетчик
        self.views_count = (self.views_count or 0) + 1
        db.session.commit()
        return True
    
    @classmethod
    def get_published(cls, limit=None, category=None, featured=None):
        """Получить опубликованные статьи"""
        query = cls.query.filter(cls.status == 'published')
        
        if category:
            query = query.filter(cls.category == category)
        
        if featured is not None:
            query = query.filter(cls.featured == featured)
        
        query = query.order_by(cls.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_by_slug(cls, slug):
        """Получить статью по slug"""
        return cls.query.filter(
            cls.slug == slug,
            cls.status == 'published'
        ).first()
    
    @classmethod
    def search(cls, query_text, limit=10):
        """Поиск статей"""
        search_filter = f"%{query_text}%"
        return cls.query.filter(
            cls.status == 'published',
            db.or_(
                cls.title.ilike(search_filter),
                cls.content.ilike(search_filter),
                cls.excerpt.ilike(search_filter)
            )
        ).order_by(cls.published_at.desc()).limit(limit).all()
    
    @classmethod
    def get_stats(cls):
        """Получить статистику блога"""
        total = cls.query.count()
        published = cls.query.filter(cls.status == 'published').count()
        draft = cls.query.filter(cls.status == 'draft').count()
        featured = cls.query.filter(cls.featured == True, cls.status == 'published').count()
        
        # Топ категории
        categories = db.session.query(
            cls.category,
            func.count(cls.id).label('count')
        ).filter(cls.status == 'published').group_by(cls.category).all()
        
        return {
            'total': total,
            'published': published,
            'draft': draft,
            'featured': featured,
            'total_views': db.session.query(func.sum(cls.views_count)).scalar() or 0,
            'categories': [{'name': cat, 'count': count} for cat, count in categories]
        }


class BlogView(db.Model):
    """Модель для детального отслеживания просмотров статей блога"""
    __tablename__ = 'blog_views'
    
    id = db.Column(db.Integer, primary_key=True)
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    ip_address = db.Column(db.String(45))  # Поддержка IPv6
    user_agent = db.Column(db.String(500))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    blog_post = db.relationship('BlogPost', backref='view_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'blog_post_id': self.blog_post_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }


class BlogComment(db.Model):
    """Модель комментариев к статьям блога (опционально)"""
    __tablename__ = 'blog_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    blog_post = db.relationship('BlogPost', backref='comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'blog_post_id': self.blog_post_id,
            'author_name': self.author_name,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
# Исправленная модель TelegramUser для models/__init__.py

class TelegramUser(db.Model):
    """Модель пользователей Telegram бота"""
    __tablename__ = 'telegram_users'
    __table_args__ = {'extend_existing': True}  # ← ИСПРАВЛЕНИЕ для избежания конфликтов
    
    # Основные поля
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Контактная информация
    phone = db.Column(db.String(20), index=True)
    email = db.Column(db.String(120))
    
    # Статус и регистрация
    is_verified = db.Column(db.Boolean, default=False, nullable=False, index=True)
    registration_step = db.Column(db.String(20), default='start', nullable=False)
    
    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime)
    
    # Настройки уведомлений
    notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    language = db.Column(db.String(10), default='ru', nullable=False)
    
    # Статистика
    messages_sent = db.Column(db.Integer, default=0, nullable=False)
    messages_received = db.Column(db.Integer, default=0, nullable=False)
    
    def __init__(self, **kwargs):
        """Инициализация пользователя"""
        super(TelegramUser, self).__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        """Строковое представление объекта"""
        return f'<TelegramUser {self.telegram_id}: {self.first_name}>'
    
    def to_dict(self, include_private=False):
        """Преобразование в словарь для API"""
        data = {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_verified': self.is_verified,
            'registration_step': self.registration_step,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'notifications_enabled': self.notifications_enabled,
            'language': self.language,
            'messages_count': self.messages_sent + self.messages_received
        }
        
        if include_private:
            data.update({
                'phone': self.phone,
                'email': self.email,
                'messages_sent': self.messages_sent,
                'messages_received': self.messages_received
            })
        
        return data
    
    def get_full_name(self):
        """Получить полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_id}"
    
    def get_display_name(self):
        """Получить отображаемое имя для интерфейса"""
        if self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_id}"
    
    def update_activity(self):
        """Обновить время последней активности"""
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except:
            db.session.rollback()
    
    def increment_sent_messages(self):
        """Увеличить счетчик отправленных сообщений"""
        self.messages_sent = (self.messages_sent or 0) + 1
        self.update_activity()
    
    def increment_received_messages(self):
        """Увеличить счетчик полученных сообщений"""
        self.messages_received = (self.messages_received or 0) + 1
        self.update_activity()
    
    def set_phone(self, phone):
        """Установить и нормализовать номер телефона"""
        import re
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        if clean_phone.startswith('8') and len(clean_phone) == 11:
            clean_phone = '+7' + clean_phone[1:]
        elif clean_phone.startswith('7') and len(clean_phone) == 11:
            clean_phone = '+' + clean_phone
        elif not clean_phone.startswith('+'):
            clean_phone = '+' + clean_phone
        
        self.phone = clean_phone
        self.updated_at = datetime.utcnow()
    
    def set_email(self, email):
        """Установить и валидировать email"""
        if email and '@' in email:
            self.email = email.lower().strip()
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def complete_registration(self):
        """Завершить процесс регистрации"""
        self.is_verified = True
        self.registration_step = 'verified'
        self.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except:
            db.session.rollback()
    
    def update_registration_step(self, step):
        """Обновить шаг регистрации"""
        valid_steps = ['start', 'phone', 'email', 'verified']
        if step in valid_steps:
            self.registration_step = step
            self.updated_at = datetime.utcnow()
            try:
                db.session.commit()
                return True
            except:
                db.session.rollback()
                return False
        return False
    
    def get_bookings(self):
        """Получить заявки пользователя"""
        if not self.phone:
            return []
        
        try:
            return Booking.query.filter_by(phone=self.phone).order_by(Booking.created_at.desc()).all()
        except:
            return []
    
    def get_bookings_count(self):
        """Получить количество заявок пользователя"""
        if not self.phone:
            return 0
        
        try:
            return Booking.query.filter_by(phone=self.phone).count()
        except:
            return 0
    
    def get_recent_bookings(self, limit=5):
        """Получить последние заявки пользователя"""
        if not self.phone:
            return []
        
        try:
            return Booking.query.filter_by(phone=self.phone).order_by(
                Booking.created_at.desc()
            ).limit(limit).all()
        except:
            return []
    
    def has_active_bookings(self):
        """Проверить наличие активных заявок"""
        if not self.phone:
            return False
        
        try:
            active_statuses = ['new', 'confirmed']
            return Booking.query.filter(
                Booking.phone == self.phone,
                Booking.status.in_(active_statuses)
            ).count() > 0
        except:
            return False
    
    def can_receive_notifications(self):
        """Проверить, может ли пользователь получать уведомления"""
        return (
            self.is_verified and 
            self.notifications_enabled and 
            self.phone is not None
        )
    
    @classmethod
    def find_by_telegram_id(cls, telegram_id):
        """Найти пользователя по Telegram ID"""
        try:
            return cls.query.filter_by(telegram_id=str(telegram_id)).first()
        except:
            return None
    
    @classmethod
    def find_by_phone(cls, phone, verified_only=True):
        """Найти пользователя по номеру телефона"""
        try:
            query = cls.query.filter_by(phone=phone)
            if verified_only:
                query = query.filter_by(is_verified=True)
            return query.first()
        except:
            return None
    
    @classmethod
    def get_verified_users(cls):
        """Получить всех верифицированных пользователей"""
        try:
            return cls.query.filter_by(is_verified=True).all()
        except:
            return []
    
    @classmethod
    def get_statistics(cls):
        """Получить статистику пользователей"""
        try:
            total = cls.query.count()
            verified = cls.query.filter_by(is_verified=True).count()
            unverified = total - verified
            
            return {
                'total': total,
                'verified': verified,
                'unverified': unverified,
                'verification_rate': round((verified / total * 100), 1) if total > 0 else 0
            }
        except:
            return {
                'total': 0,
                'verified': 0,
                'unverified': 0,
                'verification_rate': 0
            }
    
    @classmethod
    def create_from_telegram_data(cls, telegram_data):
        """Создать пользователя из данных Telegram"""
        try:
            existing_user = cls.find_by_telegram_id(telegram_data['id'])
            
            if existing_user:
                # Обновляем данные существующего пользователя
                existing_user.username = telegram_data.get('username')
                existing_user.first_name = telegram_data.get('first_name')
                existing_user.last_name = telegram_data.get('last_name')
                existing_user.updated_at = datetime.utcnow()
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                return existing_user
            
            # Создаем нового пользователя
            new_user = cls(
                telegram_id=str(telegram_data['id']),
                username=telegram_data.get('username'),
                first_name=telegram_data.get('first_name'),
                last_name=telegram_data.get('last_name'),
                registration_step='start'
            )
            
            db.session.add(new_user)
            try:
                db.session.commit()
                return new_user
            except:
                db.session.rollback()
                return None
                
        except Exception as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            return None

# Вспомогательные функции (добавьте в конец models/__init__.py)

def find_telegram_user_by_phone(phone):
    """Найти пользователя Telegram по номеру телефона"""
    return TelegramUser.find_by_phone(phone, verified_only=True)

def get_telegram_user_stats():
    """Получить статистику пользователей Telegram"""
    return TelegramUser.get_statistics()