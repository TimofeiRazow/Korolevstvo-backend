
import re
from datetime import datetime, date

def validate_phone(phone):
    """Валидация номера телефона"""
    if not phone:
        return False
    # Простая валидация для казахстанских номеров
    phone_pattern = r'^(\+7|8)[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(phone_pattern, phone.replace(' ', '')))

def validate_email(email):
    """Валидация email"""
    if not email:
        return True  # Email не обязателен
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_booking_data(data):
    """Валидация данных бронирования"""
    errors = []
    
    # Обязательные поля
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Имя должно содержать минимум 2 символа')
    
    if not data.get('phone'):
        errors.append('Номер телефона обязателен')
    elif not validate_phone(data['phone']):
        errors.append('Неверный формат номера телефона')
    
    # Проверка email если указан
    if data.get('email') and not validate_email(data['email']):
        errors.append('Неверный формат email')
    
    # Проверка даты
    if data.get('event_date'):
        try:
            event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
            if event_date < date.today():
                errors.append('Дата мероприятия не может быть в прошлом')
        except ValueError:
            errors.append('Неверный формат даты')
    
    # Проверка времени
    if data.get('event_time'):
        try:
            datetime.strptime(data['event_time'], '%H:%M')
        except ValueError:
            errors.append('Неверный формат времени')
    
    # Проверка количества гостей
    if data.get('guests_count'):
        try:
            guests = int(data['guests_count'])
            if guests < 1:
                errors.append('Количество гостей должно быть больше 0')
            elif guests > 1000:
                errors.append('Слишком большое количество гостей')
        except (ValueError, TypeError):
            errors.append('Неверный формат количества гостей')
    
    return errors

def validate_review_data(data):
    """Валидация данных отзыва"""
    errors = []
    
    # Обязательные поля
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Имя должно содержать минимум 2 символа')
    
    if not data.get('text') or len(data['text'].strip()) < 10:
        errors.append('Текст отзыва должен содержать минимум 10 символов')
    
    if len(data.get('text', '')) > 1000:
        errors.append('Текст отзыва слишком длинный (максимум 1000 символов)')
    
    # Проверка рейтинга
    rating = data.get('rating')
    if not rating:
        errors.append('Рейтинг обязателен')
    else:
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                errors.append('Рейтинг должен быть от 1 до 5')
        except (ValueError, TypeError):
            errors.append('Неверный формат рейтинга')
    
    return errors

def validate_service_request(data):
    """Валидация данных услуги"""
    errors = []
    
    if not data.get('title') or len(data['title'].strip()) < 3:
        errors.append('Название услуги должно содержать минимум 3 символа')
    
    if not data.get('category'):
        errors.append('Категория обязательна')
    
    if not data.get('description') or len(data['description'].strip()) < 20:
        errors.append('Описание должно содержать минимум 20 символов')
    
    return errors


def validate_admin_data(data):
    """Валидация данных администратора"""
    errors = []
    
    # Проверка имени
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Имя должно содержать минимум 2 символа')
    
    # Проверка email
    if not data.get('email'):
        errors.append('Email обязателен')
    elif not validate_email(data['email']):
        errors.append('Неверный формат email')
    
    # Проверка пароля
    if not data.get('password'):
        errors.append('Пароль обязателен')
    elif len(data['password']) < 6:
        errors.append('Пароль должен содержать минимум 6 символов')
    
    # Проверка роли
    valid_roles = ['admin', 'manager', 'editor', 'super_admin']
    if data.get('role') and data['role'] not in valid_roles:
        errors.append('Недопустимая роль')
    
    return errors