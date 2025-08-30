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
    # В класс Booking добавьте:
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
# Отношение source_lead уже создается через backref в модели Lead
    
    def to_dict(self):
        try:
            data = {
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
                'created_at': self.created_at.isoformat(),
                # 🆕 НОВОЕ: Информация о связанном лиде
                'lead_id': self.lead_id
            }
            
            # Добавляем краткую информацию о лиде, если он есть
            if self.source_lead:
                data['lead_info'] = {
                    'id': self.source_lead.id,
                    'status': self.source_lead.status,
                    'quality_score': self.source_lead.quality_score,
                    'temperature': self.source_lead.temperature
                }
            
            return data
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


# Добавить в models/__init__.py после существующих моделей

class WarehouseInventory(db.Model):
    """Инвентаризации склада"""
    __tablename__ = 'warehouse_inventories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Название инвентаризации
    description = db.Column(db.Text)
    
    # Статус инвентаризации
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    
    # Пользователь и временные метки
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    creator = db.relationship('Admin', foreign_keys=[created_by], backref='created_inventories')
    
    completed_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    completer = db.relationship('Admin', foreign_keys=[completed_by])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'completed_by': self.completed_by,
            'completer_name': self.completer.name if self.completer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'records_count': len(self.records)
        }


class WarehouseInventoryRecord(db.Model):
    """Записи инвентаризации"""
    __tablename__ = 'warehouse_inventory_records'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Связи
    inventory_id = db.Column(db.Integer, db.ForeignKey('warehouse_inventories.id'), nullable=False)
    inventory = db.relationship('WarehouseInventory', backref='records')
    
    item_id = db.Column(db.Integer, db.ForeignKey('warehouse_items.id'), nullable=False)
    item = db.relationship('WarehouseItem')
    
    # Количества
    system_quantity = db.Column(db.Integer, nullable=False)  # По данным системы
    actual_quantity = db.Column(db.Integer, nullable=True)   # Фактическое количество
    difference = db.Column(db.Integer, default=0)            # Разница
    
    # Статус проверки
    status = db.Column(db.String(20), default='pending')  # pending, checked, adjusted
    comment = db.Column(db.Text)
    
    checked_at = db.Column(db.DateTime)
    checked_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    checker = db.relationship('Admin')
    
    def to_dict(self):
        return {
            'id': self.id,
            'inventory_id': self.inventory_id,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'system_quantity': self.system_quantity,
            'actual_quantity': self.actual_quantity,
            'difference': self.difference,
            'status': self.status,
            'comment': self.comment,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
            'checker_name': self.checker.name if self.checker else None
        }

# В models/__init__.py - исправленная модель WarehouseItem

class WarehouseItem(db.Model):
    """Товары на складе"""
    __tablename__ = 'warehouse_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    barcode = db.Column(db.String(100), unique=True, nullable=True, index=True)
    sku = db.Column(db.String(50), unique=True, nullable=True)  # Артикул
    description = db.Column(db.Text)
    
    # Характеристики товара
    unit = db.Column(db.String(20), default='шт')  # Единица измерения
    min_quantity = db.Column(db.Integer, default=0)  # Минимальный остаток
    max_quantity = db.Column(db.Integer, default=1000)  # Максимальный остаток
    cost_price = db.Column(db.Numeric(10, 2), default=0)  # Себестоимость
    
    # Статус и метаданные
    status = db.Column(db.String(20), default='active')  # active, inactive, discontinued
    current_quantity = db.Column(db.Integer, default=0)  # Текущее количество
    reserved_quantity = db.Column(db.Integer, default=0)  # Зарезервированное количество
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_operation_at = db.Column(db.DateTime)

    def to_dict(self, include_categories=True):
        """Безопасная версия to_dict без ссылок на старое поле category"""
        try:
            data = {
                'id': self.id,
                'name': self.name or '',
                'barcode': self.barcode,
                'sku': self.sku,
                'description': self.description or '',
                'unit': self.unit or 'шт',
                'min_quantity': self.min_quantity or 0,
                'max_quantity': self.max_quantity or 1000,
                'cost_price': float(self.cost_price) if self.cost_price else 0,
                'status': self.status or 'active',
                'current_quantity': self.current_quantity or 0,
                'reserved_quantity': self.reserved_quantity or 0,
                'available_quantity': (self.current_quantity or 0) - (self.reserved_quantity or 0),
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'last_operation_at': self.last_operation_at.isoformat() if self.last_operation_at else None
            }
            
            # Добавляем информацию о категориях с обработкой ошибок
            if include_categories:
                try:
                    categories = self.get_categories()
                    data['categories'] = []
                    data['category_ids'] = []
                    data['category_names'] = []
                    
                    for cat in categories:
                        try:
                            cat_dict = cat.to_dict()
                            data['categories'].append(cat_dict)
                            data['category_ids'].append(cat.id)
                            data['category_names'].append(cat.name)
                        except Exception as e:
                            print(f"Ошибка преобразования категории {cat.id}: {e}")
                            continue
                    
                    # Для обратной совместимости - основная категория
                    if categories:
                        try:
                            main_category = categories[0]
                            data['category'] = {
                                'id': main_category.id,
                                'name': main_category.name,
                                'color': getattr(main_category, 'color', '#6366f1')
                            }
                            data['category_path'] = main_category.get_full_path()
                        except Exception as e:
                            print(f"Ошибка создания основной категории: {e}")
                            data['category'] = None
                            data['category_path'] = ''
                    else:
                        data['category'] = None
                        data['category_path'] = ''
                        
                except Exception as e:
                    print(f"Ошибка получения категорий для товара {self.id}: {e}")
                    data['categories'] = []
                    data['category_ids'] = []
                    data['category_names'] = []
                    data['category'] = None
                    data['category_path'] = ''
            
            # Статусы для UI
            data['is_low_stock'] = (self.current_quantity or 0) <= (self.min_quantity or 0)
            data['is_out_of_stock'] = (self.current_quantity or 0) == 0
            data['is_overstocked'] = (self.current_quantity or 0) > (self.max_quantity or 1000)
            
            return data
            
        except Exception as e:
            print(f"Критическая ошибка в to_dict для товара {getattr(self, 'id', 'unknown')}: {e}")
            # Возвращаем минимальный набор данных
            return {
                'id': getattr(self, 'id', None),
                'name': getattr(self, 'name', 'Ошибка загрузки'),
                'current_quantity': getattr(self, 'current_quantity', 0),
                'unit': getattr(self, 'unit', 'шт'),
                'status': getattr(self, 'status', 'active'),
                'categories': [],
                'category_names': [],
                'category': None,
                'category_path': '',
                'error': str(e)
            }
    
    def get_categories(self):
        """Безопасное получение категорий товара"""
        try:
            # Проверяем, что таблица связи существует
            if not hasattr(db.session, 'query'):
                return []
                
            categories = db.session.query(WarehouseCategory).join(
                WarehouseItemCategory,
                WarehouseCategory.id == WarehouseItemCategory.category_id
            ).filter(WarehouseItemCategory.item_id == self.id).all()
            
            return categories
            
        except Exception as e:
            print(f"Ошибка получения категорий для товара {self.id}: {e}")
            return []
    
    def add_category(self, category_id):
        """Добавить категорию к товару"""
        try:
            existing = WarehouseItemCategory.query.filter(
                WarehouseItemCategory.item_id == self.id,
                WarehouseItemCategory.category_id == category_id
            ).first()
            
            if not existing:
                item_category = WarehouseItemCategory(
                    item_id=self.id,
                    category_id=category_id
                )
                db.session.add(item_category)
                return True
            return False
        except Exception as e:
            print(f"Ошибка добавления категории {category_id} к товару {self.id}: {e}")
            return False
    
    def remove_category(self, category_id):
        """Удалить категорию у товара"""
        try:
            deleted_count = WarehouseItemCategory.query.filter(
                WarehouseItemCategory.item_id == self.id,
                WarehouseItemCategory.category_id == category_id
            ).delete()
            return deleted_count > 0
        except Exception as e:
            print(f"Ошибка удаления категории {category_id} у товара {self.id}: {e}")
            return False
    
    def set_categories(self, category_ids):
        """Установить категории товара (заменить все существующие)"""
        try:
            # Удаляем все существующие связи
            WarehouseItemCategory.query.filter(
                WarehouseItemCategory.item_id == self.id
            ).delete()
            
            # Добавляем новые связи
            for category_id in category_ids:
                if category_id:  # Проверяем что ID не пустой
                    item_category = WarehouseItemCategory(
                        item_id=self.id,
                        category_id=category_id
                    )
                    db.session.add(item_category)
            
            return True
        except Exception as e:
            print(f"Ошибка установки категорий для товара {self.id}: {e}")
            return False

    def update_quantity(self, new_quantity, operation_type, reason=None, user_id=None):
        """Обновить количество товара с записью операции"""
        try:
            old_quantity = self.current_quantity or 0
            self.current_quantity = new_quantity
            self.last_operation_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            
            # Создаем запись об операции
            operation = WarehouseOperation(
                item_id=self.id,
                operation_type=operation_type,
                quantity_before=old_quantity,
                quantity_after=new_quantity,
                quantity_change=new_quantity - old_quantity,
                reason=reason,
                user_id=user_id
            )
            
            db.session.add(operation)
            return operation
        except Exception as e:
            print(f"Ошибка обновления количества товара {self.id}: {e}")
            raise

    @classmethod
    def search(cls, query, category_ids=None, status='active'):
        """Поиск товаров с поддержкой множественных категорий"""
        try:
            search_query = cls.query.filter(cls.status == status)
            
            if category_ids:
                # Поиск товаров, которые относятся к любой из указанных категорий
                search_query = search_query.join(WarehouseItemCategory).filter(
                    WarehouseItemCategory.category_id.in_(category_ids)
                ).distinct()
            
            if query:
                search_filter = f"%{query}%"
                search_query = search_query.filter(
                    db.or_(
                        cls.name.ilike(search_filter),
                        cls.barcode.ilike(search_filter),
                        cls.sku.ilike(search_filter),
                        cls.description.ilike(search_filter)
                    )
                )
            
            return search_query
        except Exception as e:
            print(f"Ошибка поиска товаров: {e}")
            return cls.query.filter(cls.id == -1)  # Возвращаем пустой результат

    @classmethod
    def get_low_stock_items(cls):
        """Получить товары с низким остатком"""
        try:
            return cls.query.filter(
                cls.current_quantity <= cls.min_quantity,
                cls.status == 'active'
            ).all()
        except Exception as e:
            print(f"Ошибка получения товаров с низким остатком: {e}")
            return []


# Обновленная модель WarehouseOperation с исправлениями
class WarehouseOperation(db.Model):
    """История операций со складом"""
    __tablename__ = 'warehouse_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Связи
    item_id = db.Column(db.Integer, db.ForeignKey('warehouse_items.id'), nullable=False)
    item = db.relationship('WarehouseItem', backref='operations')
    user_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    user = db.relationship('Admin', backref='warehouse_operations')
    
    # Детали операции
    operation_type = db.Column(db.String(20), nullable=False)  # add, remove, transfer, adjust, reserve, unreserve
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # Может быть отрицательным
    
    # Причина и комментарий
    reason = db.Column(db.String(100))  # Причина операции
    comment = db.Column(db.Text)  # Дополнительный комментарий
    document_number = db.Column(db.String(50))  # Номер документа (накладной, заявки и т.д.)
    
    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IP адрес пользователя
    
    def to_dict(self, include_item=True, include_user=True):
        """Безопасное преобразование в словарь без ссылок на старые поля"""
        try:
            data = {
                'id': self.id,
                'item_id': self.item_id,
                'user_id': self.user_id,
                'operation_type': self.operation_type,
                'quantity_before': self.quantity_before,
                'quantity_after': self.quantity_after,
                'quantity_change': self.quantity_change,
                'reason': self.reason,
                'comment': self.comment,
                'document_number': self.document_number,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'ip_address': self.ip_address
            }
            
            if include_item and self.item:
                try:
                    # Получаем категории товара безопасно
                    categories = self.item.get_categories()
                    category_names = [cat.name for cat in categories] if categories else []
                    
                    data['item'] = {
                        'id': self.item.id,
                        'name': self.item.name,
                        'barcode': self.item.barcode,
                        'sku': self.item.sku,
                        'unit': self.item.unit,
                        'category_names': category_names
                    }
                    
                    # Для обратной совместимости
                    if categories:
                        data['item']['category'] = categories[0].name
                        data['item']['category_path'] = categories[0].get_full_path()
                    else:
                        data['item']['category'] = 'Без категории'
                        data['item']['category_path'] = 'Без категории'
                        
                except Exception as e:
                    print(f"Ошибка получения информации о товаре {self.item_id}: {e}")
                    data['item'] = {
                        'id': self.item.id,
                        'name': self.item.name or 'Неизвестный товар',
                        'category': 'Не определена',
                        'category_names': []
                    }
            
            if include_user and self.user:
                data['user'] = {
                    'id': self.user.id,
                    'name': self.user.name,
                    'email': self.user.email
                }
            
            # Читаемое описание операции
            operation_descriptions = {
                'add': 'Поступление',
                'remove': 'Списание',
                'transfer': 'Перемещение',
                'adjust': 'Корректировка',
                'reserve': 'Резервирование',
                'unreserve': 'Снятие резерва'
            }
            
            data['operation_description'] = operation_descriptions.get(self.operation_type, self.operation_type)
            
            return data
            
        except Exception as e:
            print(f"Ошибка преобразования операции {self.id}: {e}")
            return {
                'id': self.id,
                'error': str(e),
                'operation_type': getattr(self, 'operation_type', 'unknown'),
                'item_id': getattr(self, 'item_id', None)
            }

# Дополнительные функции для работы с моделями

# Обновленная функция в models/__init__.py
def create_sample_warehouse_data():
    """Создать примеры данных для склада с проверкой существования"""
    try:
        # Проверяем, есть ли уже данные склада
        existing_categories = WarehouseCategory.query.count()
        existing_items = WarehouseItem.query.count()
        
        if existing_categories > 0 or existing_items > 0:
            print("✅ Данные склада уже существуют")
            return
        
        print("🏗️ Создание примеров данных склада...")
        
        # Создаем основные категории
        categories_data = [
            {'name': 'Костюмы', 'color': '#ff6b6b', 'description': 'Карнавальные костюмы для всех возрастов'},
            {'name': 'Реквизит', 'color': '#4ecdc4', 'description': 'Реквизит для праздников и мероприятий'},
            {'name': 'Декорации', 'color': '#45b7d1', 'description': 'Декоративные элементы и фоны'},
            {'name': 'Музыкальное оборудование', 'color': '#96ceb4', 'description': 'Звуковое оборудование'},
            {'name': 'Игрушки', 'color': '#ffeaa7', 'description': 'Игрушки и развивающие материалы'},
        ]
        
        category_objects = {}
        for cat_data in categories_data:
            category = WarehouseCategory(**cat_data)
            db.session.add(category)
            db.session.flush()  # Получаем ID
            category_objects[cat_data['name']] = category
        
        # Создаем подкатегории
        subcategories_data = [
            {'name': 'Детские костюмы', 'parent_id': category_objects['Костюмы'].id, 'color': '#ff7675'},
            {'name': 'Взрослые костюмы', 'parent_id': category_objects['Костюмы'].id, 'color': '#fd79a8'},
            {'name': 'Супергерои', 'parent_id': category_objects['Костюмы'].id, 'color': '#6c5ce7'},
            {'name': 'Принцессы', 'parent_id': category_objects['Костюмы'].id, 'color': '#fd79a8'},
            {'name': 'Шары и надувные изделия', 'parent_id': category_objects['Реквизит'].id, 'color': '#00b894'},
            {'name': 'Аксессуары', 'parent_id': category_objects['Реквизит'].id, 'color': '#00cec9'},
            {'name': 'Фоны и баннеры', 'parent_id': category_objects['Декорации'].id, 'color': '#0984e3'},
            {'name': 'Фотозоны', 'parent_id': category_objects['Декорации'].id, 'color': '#74b9ff'},
        ]
        
        for subcat_data in subcategories_data:
            subcategory = WarehouseCategory(**subcat_data)
            db.session.add(subcategory)
            db.session.flush()
            category_objects[subcat_data['name']] = subcategory
        
        # Создаем товары с множественными категориями
        import time
        timestamp = int(time.time())
        
        items_data = [
            {
                'name': 'Костюм Человека-паука (детский, размер M)',
                'barcode': f'{timestamp}001',
                'sku': 'COST-SPIDER-M',
                'description': 'Детский костюм Человека-паука, размер M, возраст 6-8 лет',
                'categories': ['Детские костюмы', 'Супергерои'],
                'unit': 'шт',
                'min_quantity': 2,
                'max_quantity': 10,
                'cost_price': 15000,
                'current_quantity': 5
            },
            {
                'name': 'Костюм принцессы Эльзы (детский, размер S)',
                'barcode': f'{timestamp}002',
                'sku': 'COST-ELSA-S',
                'description': 'Детский костюм принцессы Эльзы из м/ф Холодное сердце',
                'categories': ['Детские костюмы', 'Принцессы', 'Фоны и баннеры'],
                'unit': 'шт',
                'min_quantity': 1,
                'max_quantity': 8,
                'cost_price': 18000,
                'current_quantity': 3
            },
            {
                'name': 'Воздушные шары красные (упаковка 100 шт)',
                'barcode': f'{timestamp}003',
                'sku': 'BALL-RED-100',
                'description': 'Воздушные шары красного цвета, диаметр 30см',
                'categories': ['Шары и надувные изделия', 'Реквизит'],
                'unit': 'упак',
                'min_quantity': 5,
                'max_quantity': 50,
                'cost_price': 2000,
                'current_quantity': 15
            },
            {
                'name': 'Воздушные шары синие (упаковка 100 шт)',
                'barcode': f'{timestamp}004',
                'sku': 'BALL-BLUE-100',
                'description': 'Воздушные шары синего цвета, диаметр 30см',
                'categories': ['Шары и надувные изделия', 'Реквизит'],
                'unit': 'упак',
                'min_quantity': 5,
                'max_quantity': 50,
                'cost_price': 2000,
                'current_quantity': 8
            },
            {
                'name': 'Микрофон беспроводной Shure SM58',
                'barcode': f'{timestamp}005',
                'sku': 'MIC-SHURE-SM58',
                'description': 'Профессиональный беспроводной микрофон Shure SM58',
                'categories': ['Музыкальное оборудование'],
                'unit': 'шт',
                'min_quantity': 1,
                'max_quantity': 5,
                'cost_price': 45000,
                'current_quantity': 2
            },
            {
                'name': 'Колонка портативная JBL',
                'barcode': f'{timestamp}006',
                'sku': 'SPEAKER-JBL-001',
                'description': 'Портативная Bluetooth колонка JBL для мероприятий',
                'categories': ['Музыкальное оборудование'],
                'unit': 'шт',
                'min_quantity': 1,
                'max_quantity': 3,
                'cost_price': 25000,
                'current_quantity': 1
            },
            {
                'name': 'Фотозона "Единороги"',
                'barcode': f'{timestamp}007',
                'sku': 'PHOTO-UNICORN-001',
                'description': 'Фотозона с единорогами для детских праздников',
                'categories': ['Фотозоны', 'Декорации'],
                'unit': 'шт',
                'min_quantity': 1,
                'max_quantity': 3,
                'cost_price': 35000,
                'current_quantity': 2
            },
            {
                'name': 'Набор мыльных пузырей',
                'barcode': f'{timestamp}008',
                'sku': 'BUBBLES-SET-001',
                'description': 'Набор для создания мыльных пузырей с аппаратом',
                'categories': ['Игрушки', 'Реквизит'],
                'unit': 'комплект',
                'min_quantity': 2,
                'max_quantity': 10,
                'cost_price': 8000,
                'current_quantity': 0  # Нет в наличии
            },
            {
                'name': 'Конструктор LEGO Friends',
                'barcode': f'{timestamp}009',
                'sku': 'LEGO-FRIENDS-001',
                'description': 'Большой набор LEGO Friends для детских мероприятий',
                'categories': ['Игрушки'],
                'unit': 'шт',
                'min_quantity': 1,
                'max_quantity': 5,
                'cost_price': 12000,
                'current_quantity': 4
            },
            {
                'name': 'Гелиевые шары фольгированные "С Днем Рождения"',
                'barcode': f'{timestamp}010',
                'sku': 'FOIL-BDAY-001',
                'description': 'Фольгированные шары с надписью "С Днем Рождения"',
                'categories': ['Шары и надувные изделия', 'Реквизит'],
                'unit': 'шт',
                'min_quantity': 10,
                'max_quantity': 100,
                'cost_price': 800,
                'current_quantity': 25
            },
            {
                'name': 'Маска Бэтмена',
                'barcode': f'{timestamp}011',
                'sku': 'MASK-BATMAN-001',
                'description': 'Детская маска Бэтмена из прочного пластика',
                'categories': ['Супергерои', 'Аксессуары'],
                'unit': 'шт',
                'min_quantity': 5,
                'max_quantity': 20,
                'cost_price': 3000,
                'current_quantity': 12
            },
            {
                'name': 'Корона принцессы золотая',
                'barcode': f'{timestamp}012',
                'sku': 'CROWN-GOLD-001',
                'description': 'Золотая корона принцессы с камнями',
                'categories': ['Принцессы', 'Аксессуары'],
                'unit': 'шт',
                'min_quantity': 3,
                'max_quantity': 15,
                'cost_price': 5000,
                'current_quantity': 7
            }
        ]
        
        for item_data in items_data:
            # Извлекаем категории из данных
            category_names = item_data.pop('categories', [])
            
            # Создаем товар
            item = WarehouseItem(**item_data)
            db.session.add(item)
            db.session.flush()  # Получаем ID товара
            
            # Добавляем связи с категориями
            category_ids = []
            for cat_name in category_names:
                if cat_name in category_objects:
                    category_ids.append(category_objects[cat_name].id)
                else:
                    # Создаем категорию, если не существует
                    new_category = WarehouseCategory.find_or_create_by_name(cat_name)
                    category_ids.append(new_category.id)
            
            if category_ids:
                item.set_categories(category_ids)
        
        db.session.commit()
        print(f"✅ Создано {len(categories_data)} основных категорий, {len(subcategories_data)} подкатегорий и {len(items_data)} товаров")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при создании данных склада: {e}")
        import traceback
        traceback.print_exc()


# Обновленная функция очистки данных
def clear_warehouse_data():
    """Очистить все данные склада"""
    try:
        # Удаляем в правильном порядке из-за внешних ключей
        WarehouseOperation.query.delete()
        WarehouseInventoryRecord.query.delete()
        WarehouseInventory.query.delete()
        WarehouseItemCategory.query.delete()  # Новая таблица связи
        WarehouseItem.query.delete()
        WarehouseCategory.query.delete()
        
        db.session.commit()
        print("✅ Данные склада очищены")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при очистке данных склада: {e}")


# Функция для добавления недостающих категорий к существующим товарам
def migrate_existing_items_to_multiple_categories():
    """Миграция существующих товаров для поддержки множественных категорий"""
    try:
        print("🔄 Миграция существующих товаров...")
        
        # Находим товары без связей с категориями
        items_without_categories = db.session.query(WarehouseItem).filter(
            ~WarehouseItem.id.in_(
                db.session.query(WarehouseItemCategory.item_id)
            )
        ).all()
        
        if not items_without_categories:
            print("✅ Все товары уже имеют категории")
            return
        
        # Создаем категорию "Без категории" если не существует
        default_category = WarehouseCategory.find_or_create_by_name("Без категории")
        
        # Добавляем связи для товаров без категорий
        for item in items_without_categories:
            item.add_category(default_category.id)
        
        db.session.commit()
        print(f"✅ Обновлено {len(items_without_categories)} товаров")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка миграции: {e}")


# CLI команда для проверки и исправления данных
def fix_warehouse_data():
    """Исправить проблемы с данными склада"""
    print("🔧 Проверка и исправление данных склада...")
    
    # 1. Миграция товаров без категорий
    migrate_existing_items_to_multiple_categories()
    
    # 2. Проверка целостности связей
    orphaned_relations = db.session.query(WarehouseItemCategory).filter(
        ~WarehouseItemCategory.item_id.in_(
            db.session.query(WarehouseItem.id)
        ) | ~WarehouseItemCategory.category_id.in_(
            db.session.query(WarehouseCategory.id)
        )
    ).all()
    
    if orphaned_relations:
        print(f"🗑️ Удаление {len(orphaned_relations)} неверных связей...")
        for relation in orphaned_relations:
            db.session.delete(relation)
        db.session.commit()
    
    # 3. Обновление счетчиков категорий
    categories = WarehouseCategory.query.all()
    for category in categories:
        items_count = category.get_items_count()
        print(f"📊 Категория '{category.name}': {items_count} товаров")
    
    print("✅ Проверка завершена")


# Функция для очистки данных склада (для тестирования)
def clear_warehouse_data():
    """Очистить все данные склада"""
    try:
        # Удаляем в правильном порядке из-за внешних ключей
        WarehouseOperation.query.delete()
        WarehouseInventoryRecord.query.delete()
        WarehouseInventory.query.delete()
        WarehouseItem.query.delete()
        WarehouseCategory.query.delete()
        
        db.session.commit()
        print("✅ Данные склада очищены")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при очистке данных склада: {e}")

# Функция для пересоздания данных склада
def recreate_warehouse_data():
    """Пересоздать данные склада"""
    print("🔄 Пересоздание данных склада...")
    clear_warehouse_data()
    create_sample_warehouse_data()
    print("✅ Данные склада пересозданы")

# Константы для операций
OPERATION_TYPES = {
    'add': 'Поступление',
    'remove': 'Списание', 
    'transfer': 'Перемещение',
    'adjust': 'Корректировка',
    'reserve': 'Резервирование',
    'unreserve': 'Снятие резерва'
}

REMOVAL_REASONS = [
    'Брак',
    'Выдача в производство',
    'Списание по износу',
    'Потеря',
    'Кража',
    'Передача в другой отдел',
    'Возврат поставщику',
    'Прочее'
]

ADDITION_REASONS = [
    'Закупка',
    'Возврат из производства',
    'Возврат от клиента',
    'Передача из другого отдела',
    'Находка',
    'Корректировка остатков',
    'Прочее'
]


# В models/__init__.py - обновленная модель WarehouseItem


# НОВАЯ таблица связи товаров и категорий (many-to-many)
class WarehouseItemCategory(db.Model):
    """Связь товаров и категорий (many-to-many)"""
    __tablename__ = 'warehouse_item_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('warehouse_items.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('warehouse_categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Уникальное ограничение для предотвращения дублирования
    __table_args__ = (
        db.UniqueConstraint('item_id', 'category_id', name='unique_item_category'),
    )
    
    # Связи
    item = db.relationship('WarehouseItem', backref='item_categories')
    category = db.relationship('WarehouseCategory', backref='category_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Обновленная модель категорий для поддержки связи с товарами
class WarehouseCategory(db.Model):
    """Категории товаров на складе"""
    __tablename__ = 'warehouse_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('warehouse_categories.id'), nullable=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6366f1')  # Цвет для UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Иерархические связи
    children = db.relationship('WarehouseCategory', 
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic')
    
    def to_dict(self, include_children=False):
        data = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
            
        return data
    
    def get_full_path(self):
        """Получить полный путь категории"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
    
    def get_items_count(self, include_subcategories=True):
        """Получить количество товаров в категории"""
        if include_subcategories:
            # Получаем все ID дочерних категорий
            category_ids = self.get_all_child_ids()
            category_ids.append(self.id)
            
            return db.session.query(WarehouseItem).join(WarehouseItemCategory).filter(
                WarehouseItemCategory.category_id.in_(category_ids),
                WarehouseItem.status == 'active'
            ).distinct().count()
        else:
            return db.session.query(WarehouseItem).join(WarehouseItemCategory).filter(
                WarehouseItemCategory.category_id == self.id,
                WarehouseItem.status == 'active'
            ).count()
    
    def get_all_child_ids(self):
        """Получить все ID дочерних категорий рекурсивно"""
        child_ids = []
        for child in self.children:
            child_ids.append(child.id)
            child_ids.extend(child.get_all_child_ids())
        return child_ids

    @classmethod
    def find_or_create_by_name(cls, name, parent_id=None):
        """Найти категорию по имени или создать новую"""
        category = cls.query.filter(
            cls.name == name,
            cls.parent_id == parent_id
        ).first()
        
        if not category:
            category = cls(
                name=name,
                parent_id=parent_id,
                color='#6366f1'  # Цвет по умолчанию
            )
            db.session.add(category)
            db.session.flush()  # Получаем ID
        
        return category


# models/lead.py
class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Основная информация
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(120), index=True)
    
    # Персональная информация
    birthday = db.Column(db.Date)  # День рождения лида
    age = db.Column(db.Integer)  # Возраст (для детей особенно важно)
    gender = db.Column(db.String(10))  # male, female, other
    
    # Источники привлечения
    source = db.Column(db.String(50), default='website')  # website, instagram, whatsapp, referral, google, yandex
    utm_source = db.Column(db.String(100))
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100))
    referrer = db.Column(db.String(200))  # Кто рекомендовал
    
    # Интересы и предпочтения
    interested_services = db.Column(db.JSON)  # Список интересующих услуг
    preferred_budget = db.Column(db.String(50))  # Предпочитаемый бюджет
    event_type = db.Column(db.String(50))  # birthday, wedding, corporate, anniversary
    preferred_date = db.Column(db.Date)  # Предпочитаемая дата мероприятия
    guests_count = db.Column(db.Integer)  # Ожидаемое количество гостей
    location_preference = db.Column(db.String(200))  # Предпочитаемое место
    
    # Статус и этапы воронки
    status = db.Column(db.String(20), default='new')  # new, contacted, interested, qualified, converted, lost
    stage = db.Column(db.String(20), default='awareness')  # awareness, interest, consideration, intent, evaluation, purchase
    quality_score = db.Column(db.Integer, default=0)  # Оценка качества лида (0-100)
    temperature = db.Column(db.String(10), default='cold')  # cold, warm, hot
    
    # Коммуникация
    last_contact_date = db.Column(db.DateTime)
    next_follow_up = db.Column(db.DateTime)
    contact_attempts = db.Column(db.Integer, default=0)
    preferred_contact_method = db.Column(db.String(20), default='phone')  # phone, email, whatsapp, telegram
    
    # Заметки и теги
    notes = db.Column(db.Text)
    tags = db.Column(db.JSON)  # Теги для сегментации
    
    # Назначенный менеджер
    assigned_to = db.Column(db.Integer, db.ForeignKey('admins.id'))
    assigned_manager = db.relationship('Admin', backref='assigned_leads')
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    converted_at = db.Column(db.DateTime)  # Дата конверсии в заявку
    
    # Связи
    bookings = db.relationship('Booking', backref='source_lead', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Lead, self).__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_personal=False):
        """Преобразование в словарь с возможностью скрытия персональных данных"""
        data = {
            'id': self.id,
            'name': self.name,
            'phone': self.phone if include_personal else self.phone[:3] + '***' + self.phone[-4:] if self.phone else None,
            'source': self.source,
            'interested_services': self.interested_services or [],
            'preferred_budget': self.preferred_budget,
            'event_type': self.event_type,
            'preferred_date': self.preferred_date.isoformat() if self.preferred_date else None,
            'guests_count': self.guests_count,
            'location_preference': self.location_preference,
            'status': self.status,
            'stage': self.stage,
            'quality_score': self.quality_score,
            'temperature': self.temperature,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_follow_up': self.next_follow_up.isoformat() if self.next_follow_up else None,
            'contact_attempts': self.contact_attempts,
            'preferred_contact_method': self.preferred_contact_method,
            'tags': self.tags or [],
            'assigned_to': self.assigned_to,
            'assigned_manager_name': self.assigned_manager.name if self.assigned_manager else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'bookings_count': self.bookings.count(),
            'days_since_created': (datetime.utcnow() - self.created_at).days if self.created_at else 0
        }
        
        # Персональная информация только для менеджеров
        if include_personal:
            data.update({
                'email': self.email,
                'birthday': self.birthday.isoformat() if self.birthday else None,
                'age': self.age,
                'gender': self.gender,
                'utm_source': self.utm_source,
                'utm_medium': self.utm_medium,
                'utm_campaign': self.utm_campaign,
                'referrer': self.referrer,
                'notes': self.notes
            })
            
            # Добавляем информацию о дне рождения
            if self.birthday:
                today = datetime.utcnow().date()
                this_year_birthday = self.birthday.replace(year=today.year)
                if this_year_birthday < today:
                    next_birthday = self.birthday.replace(year=today.year + 1)
                else:
                    next_birthday = this_year_birthday
                
                data.update({
                    'days_until_birthday': (next_birthday - today).days,
                    'birthday_this_year': this_year_birthday.isoformat(),
                    'is_birthday_soon': (next_birthday - today).days <= 30
                })
        
        return data
    
    def update_from_dict(self, data):
        """Обновление модели из словаря данных"""
        # Основная информация
        self.name = data.get('name', self.name)
        self.phone = data.get('phone', self.phone)
        self.email = data.get('email', self.email)
        
        # Персональная информация
        if 'birthday' in data and data['birthday']:
            try:
                if isinstance(data['birthday'], str):
                    self.birthday = datetime.fromisoformat(data['birthday'].replace('Z', '')).date()
                else:
                    self.birthday = data['birthday']
            except:
                pass
        
        self.age = data.get('age', self.age)
        self.gender = data.get('gender', self.gender)
        
        # Маркетинг
        self.source = data.get('source', self.source)
        self.utm_source = data.get('utm_source', self.utm_source)
        self.utm_medium = data.get('utm_medium', self.utm_medium)
        self.utm_campaign = data.get('utm_campaign', self.utm_campaign)
        self.referrer = data.get('referrer', self.referrer)
        
        # Предпочтения
        self.preferred_budget = data.get('preferred_budget', self.preferred_budget)
        self.event_type = data.get('event_type', self.event_type)
        self.guests_count = data.get('guests_count', self.guests_count)
        self.location_preference = data.get('location_preference', self.location_preference)
        
        if 'preferred_date' in data and data['preferred_date']:
            try:
                if isinstance(data['preferred_date'], str):
                    self.preferred_date = datetime.fromisoformat(data['preferred_date'].replace('Z', '')).date()
                else:
                    self.preferred_date = data['preferred_date']
            except:
                pass
        
        # Статус
        self.status = data.get('status', self.status)
        self.stage = data.get('stage', self.stage)
        self.quality_score = data.get('quality_score', self.quality_score)
        self.temperature = data.get('temperature', self.temperature)
        
        # Коммуникация
        self.preferred_contact_method = data.get('preferred_contact_method', self.preferred_contact_method)
        self.notes = data.get('notes', self.notes)
        self.assigned_to = data.get('assigned_to', self.assigned_to)
        
        if 'next_follow_up' in data and data['next_follow_up']:
            try:
                self.next_follow_up = datetime.fromisoformat(data['next_follow_up'].replace('Z', ''))
            except:
                pass
        
        # Обработка списковых полей
        if 'interested_services' in data:
            if isinstance(data['interested_services'], str):
                self.interested_services = [s.strip() for s in data['interested_services'].split(',') if s.strip()]
            else:
                self.interested_services = data['interested_services']
        
        if 'tags' in data:
            if isinstance(data['tags'], str):
                self.tags = [t.strip() for t in data['tags'].split(',') if t.strip()]
            else:
                self.tags = data['tags']
        
        self.updated_at = datetime.utcnow()
    
    def convert_to_booking(self, booking_data=None):
        """Конвертировать лид в заявку"""
        if self.status == 'converted':
            return None  # Уже конвертирован
        
        # Создаем заявку на основе данных лида
        booking_data = booking_data or {}
        booking = Booking(
            name=self.name,
            phone=self.phone,
            email=self.email,
            event_date=self.preferred_date,
            guests_count=self.guests_count,
            location=self.location_preference,
            budget=self.preferred_budget,
            message=booking_data.get('message', f'Конвертирован из лида #{self.id}'),
            status='new'
        )
        
        # Устанавливаем связь
        booking.source_lead = self
        
        # Обновляем статус лида
        self.status = 'converted'
        self.converted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        db.session.add(booking)
        return booking
    
    def update_contact_info(self, contact_date=None, result=None):
        """Обновить информацию о контакте"""
        self.last_contact_date = contact_date or datetime.utcnow()
        self.contact_attempts = (self.contact_attempts or 0) + 1
        
        # Автоматически планируем следующий контакт в зависимости от результата
        if result == 'answered':
            self.next_follow_up = datetime.utcnow() + timedelta(days=3)
            self.temperature = 'warm'
        elif result == 'no_answer':
            self.next_follow_up = datetime.utcnow() + timedelta(days=1)
        elif result == 'not_interested':
            self.status = 'lost'
            self.next_follow_up = None
        elif result == 'interested':
            self.next_follow_up = datetime.utcnow() + timedelta(days=1)
            self.temperature = 'hot'
            self.status = 'qualified'
        
        self.updated_at = datetime.utcnow()
    
    def calculate_quality_score(self):
        """Автоматический расчет качества лида"""
        score = 0
        
        # Источник (20 баллов максимум)
        source_scores = {
            'referral': 20,
            'google': 15,
            'instagram': 12,
            'website': 10,
            'yandex': 10,
            'whatsapp': 8,
            'other': 5
        }
        score += source_scores.get(self.source, 5)
        
        # Бюджет (25 баллов максимум)
        if self.preferred_budget:
            if '200000' in self.preferred_budget or '300000' in self.preferred_budget:
                score += 25
            elif '100000' in self.preferred_budget or '150000' in self.preferred_budget:
                score += 20
            elif '50000' in self.preferred_budget:
                score += 15
            else:
                score += 10
        
        # Полнота информации (20 баллов максимум)
        fields_filled = sum([
            bool(self.email),
            bool(self.preferred_date),
            bool(self.guests_count),
            bool(self.location_preference),
            bool(self.event_type)
        ])
        score += fields_filled * 4
        
        # Скорость ответа (15 баллов максимум)
        if self.last_contact_date and self.created_at:
            response_hours = (self.last_contact_date - self.created_at).total_seconds() / 3600
            if response_hours <= 1:
                score += 15
            elif response_hours <= 24:
                score += 10
            elif response_hours <= 72:
                score += 5
        
        # Активность (20 баллов максимум)
        if self.contact_attempts:
            if self.contact_attempts >= 3:
                score += 20
            else:
                score += self.contact_attempts * 7
        
        self.quality_score = min(score, 100)
        return self.quality_score
    
    @classmethod
    def get_stats(cls, period_days=30):
        """Получить статистику лидов"""
        date_from = datetime.utcnow() - timedelta(days=period_days)
        
        # Общая статистика
        total = cls.query.filter(cls.created_at >= date_from).count()
        converted = cls.query.filter(
            cls.created_at >= date_from,
            cls.status == 'converted'
        ).count()
        
        # По статусам
        status_stats = db.session.query(
            cls.status,
            func.count(cls.id).label('count')
        ).filter(cls.created_at >= date_from).group_by(cls.status).all()
        
        # По источникам
        source_stats = db.session.query(
            cls.source,
            func.count(cls.id).label('count')
        ).filter(cls.created_at >= date_from).group_by(cls.source).all()
        
        # По температуре
        temperature_stats = db.session.query(
            cls.temperature,
            func.count(cls.id).label('count')
        ).filter(cls.created_at >= date_from).group_by(cls.temperature).all()
        
        return {
            'total': total,
            'converted': converted,
            'conversion_rate': round((converted / total * 100), 1) if total > 0 else 0,
            'statuses': [{'status': s, 'count': c} for s, c in status_stats],
            'sources': [{'source': s, 'count': c} for s, c in source_stats],
            'temperatures': [{'temperature': t, 'count': c} for t, c in temperature_stats]
        }
    
    @classmethod
    def get_birthday_leads(cls, days_ahead=30):
        """Получить лидов с днями рождения в ближайшие дни"""
        today = datetime.utcnow().date()
        target_date = today + timedelta(days=days_ahead)
        
        # Сложный запрос для поиска дней рождения с учетом года
        leads = cls.query.filter(
            cls.birthday.isnot(None),
            cls.status.in_(['new', 'contacted', 'interested', 'qualified'])
        ).all()
        
        birthday_leads = []
        for lead in leads:
            if lead.birthday:
                # Проверяем день рождения в этом и следующем году
                this_year = lead.birthday.replace(year=today.year)
                next_year = lead.birthday.replace(year=today.year + 1)
                
                if today <= this_year <= target_date or today <= next_year <= target_date:
                    birthday_leads.append(lead)
        
        return birthday_leads
    
    @classmethod
    def find_by_phone(cls, phone):
        """Найти лид по номеру телефона"""
        return cls.query.filter(cls.phone == phone).first()
    
    @classmethod
    def create_from_booking(cls, booking):
        """Создать лид из заявки (если лид еще не существует)"""
        existing_lead = cls.find_by_phone(booking.phone)
        if existing_lead:
            return existing_lead
        
        lead = cls(
            name=booking.name,
            phone=booking.phone,
            email=booking.email,
            preferred_date=booking.event_date,
            guests_count=booking.guests_count,
            location_preference=booking.location,
            preferred_budget=booking.budget,
            event_type='birthday',  # По умолчанию для детских праздников
            source='website',
            status='converted',  # Сразу конвертирован
            converted_at=booking.created_at
        )
        
        # Связываем заявку с лидом
        booking.source_lead = lead
        
        return lead

# Обновленные функции для статистики
def get_warehouse_stats():

    """Получить общую статистику склада"""
    total_items = WarehouseItem.query.filter(WarehouseItem.status == 'active').count()
    total_categories = WarehouseCategory.query.count()
    low_stock_items = len(WarehouseItem.get_low_stock_items())
    out_of_stock_items = WarehouseItem.query.filter(
        WarehouseItem.current_quantity == 0,
        WarehouseItem.status == 'active'
    ).count()
    
    # Общая стоимость склада
    total_value = db.session.query(
        func.sum(WarehouseItem.current_quantity * WarehouseItem.cost_price)
    ).filter(WarehouseItem.status == 'active').scalar() or 0
    
    # Операции за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_operations = WarehouseOperation.query.filter(
        WarehouseOperation.created_at >= thirty_days_ago
    ).count()
    
    return {
        'total_items': total_items,
        'total_categories': total_categories,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'total_value': float(total_value),
        'recent_operations': recent_operations
    }
# Добавьте эти функции в конец models/__init__.py

def create_sample_leads_data():
    """Создать примеры данных лидов для тестирования"""
    try:
        existing_leads = Lead.query.count()
        if existing_leads > 0:
            print("✅ Данные лидов уже существуют")
            return
        
        print("🏗️ Создание примеров данных лидов...")
        
        # Получаем администраторов для назначения
        admins = Admin.query.all()
        if not admins:
            print("❌ Нет администраторов для назначения лидов")
            return
        
        # Примеры лидов
        sample_leads = [
            {
                'name': 'Анна Петрова',
                'phone': '+77771234567',
                'email': 'anna.petrova@example.com',
                'birthday': datetime(1985, 3, 15).date(),
                'age': 38,
                'source': 'instagram',
                'event_type': 'birthday',
                'preferred_budget': '150,000 ₸',
                'guests_count': 15,
                'location_preference': 'дома',
                'status': 'interested',
                'temperature': 'warm',
                'quality_score': 75,
                'interested_services': ['детский праздник', 'аниматоры'],
                'tags': ['vip', 'повторный_клиент'],
                'notes': 'Организуем день рождения дочери 8 лет'
            },
            {
                'name': 'Дмитрий Сидоров',
                'phone': '+77772345678',
                'email': 'dmitry.sidorov@example.com',
                'birthday': datetime(1992, 7, 22).date(),
                'source': 'google',
                'event_type': 'wedding',
                'preferred_budget': '500,000 ₸',
                'guests_count': 50,
                'location_preference': 'банкетный зал',
                'status': 'qualified',
                'temperature': 'hot',
                'quality_score': 90,
                'interested_services': ['свадьба', 'фотограф'],
                'preferred_date': datetime(2024, 9, 15).date()
            },
            {
                'name': 'Елена Иванова',
                'phone': '+77773456789',
                'source': 'referral',
                'referrer': 'Анна Петрова',
                'event_type': 'birthday',
                'preferred_budget': '80,000 ₸',
                'guests_count': 10,
                'status': 'new',
                'temperature': 'cold',
                'quality_score': 45,
                'interested_services': ['детский праздник'],
                'birthday': datetime(1990, 11, 8).date(),
                'notes': 'Интересуется организацией дня рождения сына 5 лет'
            },
            {
                'name': 'Максим Козлов',
                'phone': '+77774567890',
                'email': 'maxim.kozlov@company.com',
                'source': 'website',
                'event_type': 'corporate',
                'preferred_budget': '300,000 ₸',
                'guests_count': 30,
                'location_preference': 'офис компании',
                'status': 'contacted',
                'temperature': 'warm',
                'quality_score': 65,
                'interested_services': ['корпоратив', 'ведущий'],
                'birthday': datetime(1988, 4, 12).date()
            }
        ]
        
        for lead_data in sample_leads:
            lead = Lead()
            
            # Назначаем случайного администратора
            import random
            lead.assigned_to = random.choice(admins).id
            
            # Устанавливаем даты
            lead.created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            lead.updated_at = lead.created_at + timedelta(days=random.randint(0, 5))
            
            # Обновляем данные
            lead.update_from_dict(lead_data)
            
            db.session.add(lead)
        
        db.session.commit()
        print(f"✅ Создано {len(sample_leads)} примеров лидов")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при создании данных лидов: {e}")

def migrate_bookings_to_leads():
    """Создать лидов из существующих заявок"""
    try:
        print("🔄 Миграция заявок в лиды...")
        
        # Находим заявки без связанных лидов
        bookings_without_leads = Booking.query.filter(
            ~Booking.id.in_(
                db.session.query(Lead.bookings.property.mapper.class_.id)
                .filter(Lead.bookings.property.mapper.class_.lead_id.isnot(None))
            )
        ).all()
        
        created_leads = 0
        for booking in bookings_without_leads:
            existing_lead = Lead.find_by_phone(booking.phone)
            
            if not existing_lead:
                # Создаем нового лида
                lead = Lead.create_from_booking(booking)
                db.session.add(lead)
                created_leads += 1
            else:
                # Связываем с существующим лидом
                booking.lead_id = existing_lead.id
        
        db.session.commit()
        print(f"✅ Создано {created_leads} лидов из заявок")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка миграции заявок в лиды: {e}")