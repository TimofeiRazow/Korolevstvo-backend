# routes/services.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, func
from models import db, Service, Admin
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
    status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Базовый запрос
    query = Service.query
    
    # Фильтры
    if category and category != 'all':
        query = query.filter(Service.category == category)
    
    if featured:
        query = query.filter(Service.featured == True)
        
    if status:
        query = query.filter(Service.status == status)
    else:
        # По умолчанию показываем только активные услуги для публичного API
        query = query.filter(Service.status == 'active')
    
    if search:
        query = query.filter(or_(
            Service.title.contains(search),
            Service.description.contains(search)
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
    
    # Увеличиваем счетчик просмотров
    service.views_count += 1
    db.session.commit()
    
    # Получить связанные услуги той же категории
    related_services = Service.query.filter(
        and_(
            Service.category == service.category, 
            Service.id != service.id,
            Service.status == 'active'
        )
    ).limit(4).all()
    
    return jsonify({
        'service': service.to_dict(),
        'related_services': [s.to_dict() for s in related_services]
    })

# АДМИНИСТРАТИВНЫЕ МАРШРУТЫ ДЛЯ УПРАВЛЕНИЯ УСЛУГАМИ

@services_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_admin_services():
    """Получить все услуги для админки (включая неактивные)"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Базовый запрос без фильтра статуса
    query = Service.query
    
    # Фильтры
    if category and category != 'all':
        query = query.filter(Service.category == category)
        
    if status and status != 'all':
        query = query.filter(Service.status == status)
    
    if search:
        query = query.filter(or_(
            Service.title.contains(search),
            Service.description.contains(search),
            Service.category.contains(search)
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
            'has_prev': pagination.has_prev
        }
    })

@services_bp.route('/admin', methods=['POST'])
@jwt_required()
def create_service():
    """Создать новую услугу"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    # Валидация обязательных полей
    required_fields = ['title', 'category', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Поле {field} обязательно'}), 400
    
    try:
        service = Service()
        service.update_from_dict(data)
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            'message': 'Услуга успешно создана',
            'service': service.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при создании услуги: {str(e)}'}), 500

@services_bp.route('/admin/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    """Обновить услугу"""
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    try:
        service.update_from_dict(data)
        db.session.commit()
        
        return jsonify({
            'message': 'Услуга успешно обновлена',
            'service': service.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при обновлении услуги: {str(e)}'}), 500

@services_bp.route('/admin/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    """Удалить услугу"""
    service = Service.query.get_or_404(service_id)
    
    try:
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({'message': 'Услуга успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при удалении услуги: {str(e)}'}), 500

@services_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_services_stats():
    """Получить статистику услуг для админки"""
    total_services = Service.query.count()
    active_services = Service.query.filter(Service.status == 'active').count()
    featured_services = Service.query.filter(Service.featured == True).count()
    total_views = db.session.query(func.sum(Service.views_count)).scalar() or 0
    
    # Статистика по категориям
    categories_stats = db.session.query(
        Service.category,
        func.count(Service.id).label('count')
    ).group_by(Service.category).all()
    
    return jsonify({
        'total_services': total_services,
        'active_services': active_services,
        'featured_services': featured_services,
        'total_views': total_views,
        'categories_stats': [
            {'category': cat, 'count': count} 
            for cat, count in categories_stats
        ]
    })

@services_bp.route('/admin/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_services():
    """Массовое обновление услуг"""
    data = request.get_json()
    service_ids = data.get('service_ids', [])
    update_data = data.get('update_data', {})
    
    if not service_ids or not update_data:
        return jsonify({'error': 'Не указаны услуги или данные для обновления'}), 400
    
    try:
        services = Service.query.filter(Service.id.in_(service_ids)).all()
        
        for service in services:
            if 'status' in update_data:
                service.status = update_data['status']
            if 'featured' in update_data:
                service.featured = update_data['featured']
            if 'category' in update_data:
                service.category = update_data['category']
                
        db.session.commit()
        
        return jsonify({
            'message': f'Обновлено {len(services)} услуг',
            'updated_count': len(services)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при массовом обновлении: {str(e)}'}), 500

@services_bp.route('/admin/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_services():
    """Массовое удаление услуг"""
    data = request.get_json()
    service_ids = data.get('service_ids', [])
    
    if not service_ids:
        return jsonify({'error': 'Не указаны услуги для удаления'}), 400
    
    try:
        deleted_count = Service.query.filter(Service.id.in_(service_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'message': f'Удалено {deleted_count} услуг',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при массовом удалении: {str(e)}'}), 500

# ОСТАЛЬНЫЕ СУЩЕСТВУЮЩИЕ МАРШРУТЫ

@services_bp.route('/categories', methods=['GET'])
def get_categories():
    """Получить список категорий с количеством услуг"""
    categories_data = db.session.query(
        Service.category,
        func.count(Service.id).label('count')
    ).filter(Service.status == 'active').group_by(Service.category).all()
    
    categories = [
        {'id': 'all', 'name': 'Все услуги', 'count': Service.query.filter(Service.status == 'active').count()}
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
    
    services = Service.query.filter(
        and_(Service.featured == True, Service.status == 'active')
    ).limit(limit).all()
    
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
    
    query = Service.query.filter(
        and_(
            or_(
                Service.title.contains(query_text),
                Service.description.contains(query_text)
            ),
            Service.status == 'active'
        )
    )
    
    if category and category != 'all':
        query = query.filter(Service.category == category)
    
    services = query.limit(limit).all()
    
    return jsonify({
        'services': [service.to_dict() for service in services],
        'query': query_text,
        'total_found': len(services)
    })