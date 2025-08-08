from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
import jwt

def token_required(f):
    """
    Декоратор для проверки наличия валидного токена
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return '', 204
        token = None
        # Проверяем заголовок Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'error': 'Неверный формат токена'}), 401
        
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """
    Декоратор для проверки прав администратора
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return '', 204
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(allowed_roles):
    """
    Декоратор для проверки конкретных ролей
    
    Args:
        allowed_roles (list): Список разрешенных ролей
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            current_admin = getattr(request, 'current_admin', None)
            
            if not current_admin:
                return jsonify({'error': 'Необходима аутентификация'}), 403
            
            if current_admin.role not in allowed_roles:
                return jsonify({'error': 'Недостаточно прав доступа'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def can_manage_reviews(f):
    """
    Декоратор для проверки прав на управление отзывами
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        current_admin = getattr(request, 'current_admin', None)
        
        if not current_admin:
            return jsonify({'error': 'Необходимы права администратора'}), 403
        
        # Проверяем права на управление отзывами
        allowed_roles = ['admin', 'super_admin', 'moderator']
        if current_admin.role not in allowed_roles:
            return jsonify({'error': 'Недостаточно прав для управления отзывами'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def can_delete_reviews(f):
    """
    Декоратор для проверки прав на удаление отзывов
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        current_admin = getattr(request, 'current_admin', None)
        
        if not current_admin:
            return jsonify({'error': 'Необходимы права администратора'}), 403
        
        # Только админы и супер-админы могут удалять отзывы
        allowed_roles = ['admin', 'super_admin']
        if current_admin.role not in allowed_roles:
            return jsonify({'error': 'Недостаточно прав для удаления отзывов'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def check_admin_permissions(action, resource=None):
    """
    Универсальная функция проверки прав администратора
    
    Args:
        action (str): Действие (create, read, update, delete)
        resource (str): Ресурс (reviews, bookings, users, etc.)
    
    Returns:
        bool: True если есть права
    """
    current_admin = getattr(request, 'current_admin', None)
    
    if not current_admin:
        return False
    
    # Супер-админ может все
    if current_admin.role == 'super_admin':
        return True
    
    # Матрица прав для разных ролей
    permissions = {
        'admin': {
            'reviews': ['create', 'read', 'update', 'delete'],
            'bookings': ['create', 'read', 'update', 'delete'],
            'portfolio': ['create', 'read', 'update', 'delete'],
            'blog': ['create', 'read', 'update', 'delete'],
            'promotions': ['create', 'read', 'update', 'delete'],
            'settings': ['read', 'update'],
            'users': ['read'],
            'analytics': ['read']
        },
        'moderator': {
            'reviews': ['read', 'update'],
            'bookings': ['read', 'update'],
            'portfolio': ['read'],
            'blog': ['read'],
            'promotions': ['read'],
            'analytics': ['read']
        },
        'editor': {
            'reviews': ['read'],
            'portfolio': ['create', 'read', 'update'],
            'blog': ['create', 'read', 'update'],
            'promotions': ['create', 'read', 'update']
        }
    }
    
    user_permissions = permissions.get(current_admin.role, {})
    resource_permissions = user_permissions.get(resource, [])
    
    return action in resource_permissions

def log_admin_action(action, resource, resource_id=None, details=None):
    """
    Логирование действий администратора
    
    Args:
        action (str): Действие
        resource (str): Ресурс
        resource_id (int): ID ресурса
        details (dict): Дополнительные детали
    """
    current_admin = getattr(request, 'current_admin', None)
    
    if not current_admin:
        return
    
    # Импортируем модель для логов
    try:
        from models import AdminLog
        
        log_entry = AdminLog(
            admin_id=current_admin.id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        from models import db
        db.session.add(log_entry)
        db.session.commit()
        
    except Exception as e:
        print(f"Ошибка логирования действия администратора: {e}")

def rate_limit_admin(max_requests=100, window=3600):
    """
    Ограничение частоты запросов для администраторов
    
    Args:
        max_requests (int): Максимальное количество запросов
        window (int): Временное окно в секундах
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_admin = getattr(request, 'current_admin', None)
            
            if not current_admin:
                return jsonify({'error': 'Необходима аутентификация'}), 401
            
            # Здесь можно реализовать логику rate limiting
            # Например, используя Redis или в памяти
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator