# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
            'features': self.features,
            'subcategories': self.subcategories,
            'images': self.images,
            'coverImage': self.cover_image,
            'featured': self.featured,
            'tags': self.tags,
            'packages': self.packages
        }

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
    
    def to_dict_admin(self):
        """Полная информация для админки"""
        return self.to_dict(include_personal_info=True)
    
    def to_dict_public(self):
        """Публичная информация без персональных данных"""
        return self.to_dict(include_personal_info=False)
    
    def mark_helpful(self):
        """Отметить отзыв как полезный"""
        self.helpful_count += 1
        db.session.commit()
    
    def toggle_featured(self):
        """Переключить статус избранного"""
        self.featured = not self.featured
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def approve(self):
        """Одобрить отзыв"""
        self.approved = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def reject(self):
        """Отклонить отзыв (удалить)"""
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def get_stats(cls):
        """Получить статистику отзывов"""
        from sqlalchemy import func
        
        stats = db.session.query(
            func.count(cls.id).label('total'),
            func.count(cls.id).filter(cls.approved == True).label('approved'),
            func.count(cls.id).filter(cls.approved == False).label('pending'),
            func.avg(cls.rating).filter(cls.approved == True).label('avg_rating')
        ).first()
        
        return {
            'total': stats.total or 0,
            'approved': stats.approved or 0,
            'pending': stats.pending or 0,
            'average_rating': round(float(stats.avg_rating), 2) if stats.avg_rating else 0
        }
    
    @classmethod
    def get_featured(cls, limit=6):
        """Получить избранные отзывы"""
        return cls.query.filter(
            cls.approved == True,
            cls.featured == True
        ).order_by(
            cls.rating.desc(),
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_recent_approved(cls, limit=10):
        """Получить недавние одобренные отзывы"""
        return cls.query.filter(
            cls.approved == True
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
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
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    guests = db.Column(db.String(50))
    budget = db.Column(db.String(50))
    rating = db.Column(db.Integer, default=5)
    description = db.Column(db.Text)
    tags = db.Column(db.JSON)
    images = db.Column(db.JSON)
    cover_image = db.Column(db.String(500))
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'date': self.date.isoformat(),
            'location': self.location,
            'guests': self.guests,
            'budget': self.budget,
            'rating': self.rating,
            'description': self.description,
            'tags': self.tags,
            'images': self.images,
            'coverImage': self.cover_image,
            'featured': self.featured
        }

# models/team.py
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