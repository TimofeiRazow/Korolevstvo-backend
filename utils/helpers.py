import uuid
import os
from datetime import datetime
from flask import request, current_app
import re

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
    

def get_client_ip(request):
    """Получение IP адреса клиента"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_database_type():
    """Определение типа используемой базы данных"""
    from models import db
    try:
        return db.engine.name
    except:
        return 'sqlite'  # По умолчанию

def safe_db_query(query_func, default_value=None, error_message="Database query error"):
    """Безопасное выполнение запроса к базе данных"""
    try:
        return query_func()
    except Exception as e:
        print(f"{error_message}: {e}")
        return default_value

def format_month_year(date_string):
    """Форматирование строки месяца в читаемый вид"""
    try:
        from datetime import datetime
        if not date_string or date_string == 'N/A':
            return 'Не указано'
        
        # Если формат YYYY-MM
        if len(date_string) == 7 and '-' in date_string:
            year, month = date_string.split('-')
            month_names = {
                '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
                '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
                '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
            }
            return f"{month_names.get(month, month)} {year}"
        
        return date_string
    except:
        return date_string

def paginate_query_safe(query, page=1, per_page=20):
    """Безопасная пагинация запросов с обработкой ошибок"""
    try:
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': pagination.items,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    except Exception as e:
        print(f"Pagination error: {e}")
        return {
            'items': [],
            'pagination': {
                'page': 1,
                'pages': 1,
                'per_page': per_page,
                'total': 0,
                'has_next': False,
                'has_prev': False
            }
        }

def validate_pagination_params(page, per_page, max_per_page=100):
    """Валидация параметров пагинации"""
    try:
        page = max(1, int(page) if page else 1)
        per_page = min(max_per_page, max(1, int(per_page) if per_page else 20))
        return page, per_page
    except (ValueError, TypeError):
        return 1, 20

def clean_html_tags(text):
    """Удаление HTML тегов из текста"""
    import re
    if not text:
        return ""
    
    # Удаляем HTML теги
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Убираем лишние пробелы
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def truncate_text(text, max_length=150, suffix="..."):
    """Обрезка текста до указанной длины"""
    if not text:
        return ""
    
    clean_text = clean_html_tags(text)
    
    if len(clean_text) <= max_length:
        return clean_text
    
    # Обрезаем по словам
    words = clean_text.split()
    truncated = ""
    
    for word in words:
        if len(truncated + word + " ") > max_length:
            break
        truncated += word + " "
    
    return truncated.strip() + suffix