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
                'service_title': self.service.title if self.service else None,
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
    def get_by_service(cls, service_id, limit=None):
        """Получить отзывы по услуге"""
        query = cls.query.filter(
            cls.service_id == service_id,
            cls.approved == True
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def search(cls, query_text, limit=20):
        """Поиск отзывов по тексту"""
        from sqlalchemy import or_
        
        return cls.query.filter(
            cls.approved == True,
            or_(
                cls.name.contains(query_text),
                cls.text.contains(query_text),
                cls.service_type.contains(query_text)
            )
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Review {self.id}: {self.name} - {self.rating}★>'
    

# models/portfolio.py
class Portfolio(db.Model):
    __tablename__ = 'portfolio'
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value
        }