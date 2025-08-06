import uuid
import os
from datetime import datetime
from flask import request, current_app

def generate_booking_number():
    """Генерация уникального номера заявки"""
    return f"BK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def allowed_file(filename):
    """Проверка разрешенных расширений файлов"""
    ALLOWED_EXTENSIONS = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def paginate_query(query, page=1, per_page=20):
    """Пагинация запроса"""
    page = max(1, page)
    per_page = min(per_page, current_app.config.get('MAX_PAGE_SIZE', 100))
    
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def format_phone_number(phone):
    """Форматирование номера телефона"""
    if not phone:
        return None
    
    # Удаляем все символы кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Приводим к стандартному формату
    if cleaned.startswith('8'):
        cleaned = '+7' + cleaned[1:]
    elif cleaned.startswith('7'):
        cleaned = '+' + cleaned
    
    return cleaned

def get_client_ip():
    """Получение IP адреса клиента"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-Ip'):
        return request.headers.get('X-Real-Ip')
    else:
        return request.remote_addr

def format_currency(amount):
    """Форматирование суммы в тенге"""
    if not amount:
        return "0 ₸"
    
    try:
        amount = int(amount)
        return f"{amount:,} ₸".replace(',', ' ')
    except (ValueError, TypeError):
        return str(amount)