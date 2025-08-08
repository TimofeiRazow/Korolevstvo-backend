
import re
from datetime import datetime, date



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


import re
from email_validator import validate_email, EmailNotValidError

def validate_review_data(data):
    """Валидация данных отзыва"""
    errors = []
    
    # Проверка обязательных полей
    if not data.get('name'):
        errors.append('Имя обязательно для заполнения')
    elif len(data['name'].strip()) < 2:
        errors.append('Имя должно содержать минимум 2 символа')
    elif len(data['name'].strip()) > 100:
        errors.append('Имя не должно превышать 100 символов')
    
    if not data.get('text'):
        errors.append('Текст отзыва обязателен для заполнения')
    elif len(data['text'].strip()) < 10:
        errors.append('Текст отзыва должен содержать минимум 10 символов')
    elif len(data['text'].strip()) > 2000:
        errors.append('Текст отзыва не должен превышать 2000 символов')
    
    if not data.get('rating'):
        errors.append('Рейтинг обязателен для заполнения')
    else:
        try:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                errors.append('Рейтинг должен быть от 1 до 5')
        except (ValueError, TypeError):
            errors.append('Рейтинг должен быть числом от 1 до 5')
    
    # Проверка email если предоставлен
    if data.get('email'):
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            errors.append('Некорректный email адрес')
    
    # Проверка типа услуги если предоставлен
    if data.get('service_type') and len(data['service_type'].strip()) > 100:
        errors.append('Тип услуги не должен превышать 100 символов')
    
    # Проверка на недопустимые символы в имени
    if data.get('name') and not re.match(r'^[а-яА-Яa-zA-Z0-9\s\-_.]+$', data['name']):
        errors.append('Имя содержит недопустимые символы')
    
    return errors

def validate_booking_data(data):
    """Валидация данных бронирования"""
    errors = []
    
    # Обязательные поля
    if not data.get('name'):
        errors.append('Имя обязательно для заполнения')
    elif len(data['name'].strip()) < 2:
        errors.append('Имя должно содержать минимум 2 символа')
    
    if not data.get('phone'):
        errors.append('Телефон обязателен для заполнения')
    
    # Email если предоставлен
    if data.get('email'):
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            errors.append('Некорректный email адрес')
    
    # Количество гостей
    if data.get('guests_count'):
        try:
            guests = int(data['guests_count'])
            if guests < 1 or guests > 1000:
                errors.append('Количество гостей должно быть от 1 до 1000')
        except (ValueError, TypeError):
            errors.append('Количество гостей должно быть числом')
    
    return errors

def validate_phone(phone):
    """Валидация номера телефона"""
    if not phone:
        return False
    
    # Удаляем все не цифры
    clean_phone = re.sub(r'\D', '', phone)
    
    # Проверяем длину (казахстанские номера)
    if len(clean_phone) == 11 and clean_phone.startswith('7'):
        return True
    elif len(clean_phone) == 10 and clean_phone.startswith('7'):
        return True
    
    return False

def sanitize_input(text):
    """Очистка входных данных от потенциально опасного контента"""
    if not text:
        return text
    
    # Удаляем HTML теги
    text = re.sub(r'<[^>]*>', '', text)
    
    # Удаляем скрипты
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Ограничиваем длину строк
    if len(text) > 5000:
        text = text[:5000]
    
    return text.strip()

def validate_admin_data(data):
    """Валидация данных администратора"""
    errors = []
    
    if not data.get('name'):
        errors.append('Имя обязательно для заполнения')
    
    if not data.get('email'):
        errors.append('Email обязателен для заполнения')
    else:
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            errors.append('Некорректный email адрес')
    
    if data.get('password') and len(data['password']) < 6:
        errors.append('Пароль должен содержать минимум 6 символов')
    
    allowed_roles = ['admin', 'manager', 'editor']
    if data.get('role') and data['role'] not in allowed_roles:
        errors.append(f'Роль должна быть одной из: {", ".join(allowed_roles)}')
    
    return errors


# utils/validators.py - Валидатор для отзывов

import re
from typing import Dict, List

def validate_review_data(data: dict) -> List[str]:
    """
    Валидация данных отзыва
    
    Args:
        data: Словарь с данными отзыва
        
    Returns:
        List[str]: Список ошибок валидации
    """
    errors = []
    
    # Проверка обязательных полей
    required_fields = ['name', 'rating', 'text']
    for field in required_fields:
        if not data.get(field):
            field_names = {
                'name': 'Имя',
                'rating': 'Оценка',
                'text': 'Текст отзыва'
            }
            errors.append(f'Поле "{field_names[field]}" обязательно для заполнения')
    
    # Валидация имени
    if data.get('name'):
        name = data['name'].strip()
        if len(name) < 2:
            errors.append('Имя должно содержать минимум 2 символа')
        if len(name) > 100:
            errors.append('Имя не должно превышать 100 символов')
        if not re.match(r'^[а-яА-Я\s\-\.a-zA-Z]+$', name):
            errors.append('Имя может содержать только буквы, пробелы, тире и точки')
    
    # Валидация рейтинга
    if data.get('rating'):
        try:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                errors.append('Оценка должна быть от 1 до 5')
        except (ValueError, TypeError):
            errors.append('Оценка должна быть числом от 1 до 5')
    
    # Валидация текста отзыва
    if data.get('text'):
        text = data['text'].strip()
        if len(text) < 10:
            errors.append('Текст отзыва должен содержать минимум 10 символов')
        if len(text) > 2000:
            errors.append('Текст отзыва не должен превышать 2000 символов')
    
    # Валидация email (если указан)
    if data.get('email'):
        email = data['email'].strip()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append('Некорректный формат email')
        if len(email) > 120:
            errors.append('Email не должен превышать 120 символов')
    
    # Валидация телефона (если указан)
    if data.get('phone'):
        phone = data['phone'].strip()
        # Убираем все символы кроме цифр и +
        phone_clean = re.sub(r'[^\d+]', '', phone)
        if phone_clean:
            if not re.match(r'^\+?[7-8][\d\s\-\(\)]{10,14}$', phone):
                errors.append('Некорректный формат телефона')
            if len(phone_clean) > 20:
                errors.append('Телефон не должен превышать 20 символов')
    
    # Валидация типа услуги (если указан)
    if data.get('service_type'):
        service_type = data['service_type'].strip()
        if len(service_type) > 100:
            errors.append('Тип услуги не должен превышать 100 символов')
        
        # Проверяем, что тип услуги из разрешенного списка
        allowed_services = [
            'Детские праздники',
            'Свадебные торжества', 
            'Корпоративные мероприятия',
            'Юбилеи и торжества',
            'Квесты и игры',
            'Шоу-программы',
            'Праздничные программы',
            'Дополнительные услуги'
        ]
        
        if service_type and service_type not in allowed_services:
            errors.append('Указан неизвестный тип услуги')
    
    return errors

def is_spam_text(text: str) -> bool:
    """
    Проверка текста на спам
    
    Args:
        text: Текст для проверки
        
    Returns:
        bool: True если текст похож на спам
    """
    text_lower = text.lower()
    
    # Паттерны спама
    spam_patterns = [
        # Ссылки
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        # Спам слова
        r'\b(?:реклама|спам|casino|viagra|loan|credit|money|заработок|доходы)\b',
        # Много заглавных букв
        r'[A-ZА-Я]{5,}',
        # Повторяющиеся символы
        r'(.)\1{4,}',
        # Подозрительные символы
        r'[^\w\s\.,!?\-\(\)\'\"№]+',
        # Номера телефонов в тексте (кроме российских)
        r'\b\d{3}-\d{3}-\d{4}\b',
        # Подозрительные домены
        r'\b(?:\.tk|\.ml|\.ga|\.cf)\b'
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE | re.UNICODE):
            return True
    
    # Проверка на слишком много одинаковых слов
    words = text_lower.split()
    if len(words) > 5:
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Считаем только длинные слова
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Если какое-то слово повторяется больше 30% от общего количества
        max_repeats = max(word_counts.values()) if word_counts else 0
        if max_repeats > len(words) * 0.3:
            return True
    
    return False

def validate_review_bulk_operation(data: dict) -> List[str]:
    """
    Валидация для массовых операций с отзывами
    
    Args:
        data: Данные для массовой операции
        
    Returns:
        List[str]: Список ошибок валидации
    """
    errors = []
    
    if not data.get('review_ids'):
        errors.append('Не указаны ID отзывов для операции')
        return errors
    
    review_ids = data['review_ids']
    
    if not isinstance(review_ids, list):
        errors.append('ID отзывов должны быть переданы в виде списка')
        return errors
    
    if len(review_ids) == 0:
        errors.append('Список ID отзывов не должен быть пустым')
    
    if len(review_ids) > 100:
        errors.append('Нельзя обработать более 100 отзывов за одну операцию')
    
    # Проверяем, что все ID являются числами
    for review_id in review_ids:
        try:
            int(review_id)
        except (ValueError, TypeError):
            errors.append(f'Некорректный ID отзыва: {review_id}')
            break
    
    return errors

def sanitize_review_data(data: dict) -> dict:
    """
    Очистка и нормализация данных отзыва
    
    Args:
        data: Исходные данные
        
    Returns:
        dict: Очищенные данные
    """
    sanitized = {}
    
    # Очистка строковых полей
    string_fields = ['name', 'text', 'service_type', 'email', 'phone']
    for field in string_fields:
        if data.get(field):
            value = str(data[field]).strip()
            # Удаляем лишние пробелы
            value = re.sub(r'\s+', ' ', value)
            sanitized[field] = value
        else:
            sanitized[field] = None
    
    # Обработка рейтинга
    if data.get('rating'):
        try:
            sanitized['rating'] = max(1, min(5, int(data['rating'])))
        except (ValueError, TypeError):
            sanitized['rating'] = 5
    else:
        sanitized['rating'] = 5
    
    # Обработка булевых полей
    bool_fields = ['approved', 'featured']
    for field in bool_fields:
        if field in data:
            sanitized[field] = bool(data[field])
    
    # Обработка числовых полей
    if data.get('service_id'):
        try:
            sanitized['service_id'] = int(data['service_id'])
        except (ValueError, TypeError):
            sanitized['service_id'] = None
    
    return sanitized