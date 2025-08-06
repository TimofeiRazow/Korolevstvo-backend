from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_
from models import db, Service
from utils.validators import validate_service_request
from utils.helpers import paginate_query

services_bp = Blueprint('services', __name__)

@services_bp.route('/', methods=['GET'])
def get_services():
    """Получить список услуг с фильтрацией и пагинацией"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    category = request.args.get('category')
    featured = request.args.get('featured', type=bool)
    search = request.args.get('search', '').strip()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Базовый запрос
    query = Service.query
    
    # Фильтры
    if category and category != 'all':
        query = query.filter(Service.category == category)
    
    if featured:
        query = query.filter(Service.featured == True)
    
    if search:
        query = query.filter(or_(
            Service.title.contains(search),
            Service.description.contains(search),
            Service.tags.contains(search)
        ))
    
    # Сортировка
    sort_column = getattr(Service, sort_by, Service.created_at)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Пагинация
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    services = [service.to_dict() for service in pagination.items]
    
    return jsonify({
        'services': services,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_page': pagination.next_num if pagination.has_next else None,
            'prev_page': pagination.prev_num if pagination.has_prev else None
        }
    })

@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    """Получить детали услуги"""
    service = Service.query.get_or_404(service_id)
    
    # Получить связанные услуги той же категории
    related_services = Service.query.filter(
        and_(Service.category == service.category, Service.id != service.id)
    ).limit(4).all()
    
    return jsonify({
        'service': service.to_dict(),
        'related_services': [s.to_dict() for s in related_services]
    })

@services_bp.route('/categories', methods=['GET'])
def get_categories():
    """Получить список категорий с количеством услуг"""
    from sqlalchemy import func
    
    categories_data = db.session.query(
        Service.category,
        func.count(Service.id).label('count')
    ).group_by(Service.category).all()
    
    categories = [
        {'id': 'all', 'name': 'Все услуги', 'count': Service.query.count()}
    ]
    
    category_names = {
        'children': 'Детские',
        'weddings': 'Свадьбы',
        'corporate': 'Корпоративы',
        'anniversaries': 'Юбилеи',
        'seasonal': 'Праздники',
        'quests': 'Квесты',
        'photo': 'Фото/Видео',
        'decoration': 'Декор',
        'characters': 'Персонажи',
        'shows': 'Шоу',
        'balloons': 'Шары',
        'animators': 'Аниматоры'
    }
    
    for category, count in categories_data:
        categories.append({
            'id': category,
            'name': category_names.get(category, category.title()),
            'count': count
        })
    
    return jsonify({'categories': categories})

@services_bp.route('/featured', methods=['GET'])
def get_featured_services():
    """Получить рекомендуемые услуги"""
    limit = request.args.get('limit', 6, type=int)
    
    services = Service.query.filter(Service.featured == True).limit(limit).all()
    
    return jsonify({
        'services': [service.to_dict() for service in services]
    })

@services_bp.route('/search', methods=['GET'])
def search_services():
    """Поиск услуг"""
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category')
    limit = request.args.get('limit', 10, type=int)
    
    if not query_text:
        return jsonify({'services': []})
    
    query = Service.query.filter(or_(
        Service.title.contains(query_text),
        Service.description.contains(query_text),
        Service.tags.contains(query_text)
    ))
    
    if category and category != 'all':
        query = query.filter(Service.category == category)
    
    services = query.limit(limit).all()
    
    return jsonify({
        'services': [service.to_dict() for service in services],
        'query': query_text,
        'total_found': len(services)
    })

@services_bp.route('/calculate', methods=['POST'])
def calculate_price():
    """Калькулятор стоимости услуг"""
    data = request.get_json()
    
    service_id = data.get('service_id')
    guests_count = data.get('guests_count', 10)
    duration = data.get('duration', 2)
    extras = data.get('extras', [])
    
    if not service_id:
        return jsonify({'error': 'service_id is required'}), 400
    
    service = Service.query.get_or_404(service_id)
    
    # Базовая стоимость (простая логика для демонстрации)
    base_price = 50000  # Базовая цена в тенге
    
    # Расчет по количеству гостей
    if guests_count > 10:
        base_price += (guests_count - 10) * 2000
    
    # Расчет по времени
    if duration > 2:
        base_price += (duration - 2) * 10000
    
    # Дополнительные услуги
    extras_price = 0
    extra_services = {
        'photo': 25000,
        'video': 35000,
        'decoration': 20000,
        'music': 15000,
        'animator': 18000
    }
    
    for extra in extras:
        extras_price += extra_services.get(extra, 0)
    
    total_price = base_price + extras_price
    
    return jsonify({
        'service': service.to_dict(),
        'calculation': {
            'base_price': base_price,
            'extras_price': extras_price,
            'total_price': total_price,
            'guests_count': guests_count,
            'duration': duration,
            'extras': extras
        }
    })

@services_bp.route('/popular', methods=['GET'])
def get_popular_services():
    """Получить популярные услуги на основе количества заказов"""
    from sqlalchemy import func
    from models import Booking
    
    # Услуги с наибольшим количеством бронирований
    popular_services = db.session.query(
        Service,
        func.count(Booking.id).label('bookings_count')
    ).outerjoin(Booking).group_by(Service.id).order_by(
        func.count(Booking.id).desc()
    ).limit(8).all()
    
    services_data = []
    for service, bookings_count in popular_services:
        service_dict = service.to_dict()
        service_dict['bookings_count'] = bookings_count
        services_data.append(service_dict)
    
    return jsonify({
        'services': services_data
    })