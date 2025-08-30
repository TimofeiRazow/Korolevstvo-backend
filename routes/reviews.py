from flask import Blueprint, request, jsonify
from sqlalchemy import desc, func
from models import db, Review, Service
from utils.validators import validate_review_data
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import desc, func, or_, and_
from models import db, Review, Service
from utils.auth import admin_required, token_required
import re
import csv
import io

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/', methods=['GET', 'OPTIONS'])
def get_reviews():
    """Получить список отзывов с фильтрацией и пагинацией"""
    if request.method == "OPTIONS":
        return '', 204  # preflight OK без редиректов
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    service_id = request.args.get('service_id', type=int)
    rating = request.args.get('rating', type=int)
    approved_only = request.args.get('approved_only', True, type=bool)
    
    # Базовый запрос
    query = Review.query
    
    # Фильтры
    if approved_only:
        query = query.filter(Review.approved == True)
    
    if service_id:
        query = query.filter(Review.service_id == service_id)
    
    if rating:
        query = query.filter(Review.rating == rating)
    
    # Сортировка по дате (новые первые)
    query = query.order_by(desc(Review.created_at))
    
    # Пагинация
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    reviews = [review.to_dict() for review in pagination.items]
    
    return jsonify({
        'reviews': reviews,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

@reviews_bp.route('/send', methods=['POST', 'OPTIONS'])
def create_review():
    if request.method == "OPTIONS":
        return '', 204  # preflight OK без редиректов
    """Добавить новый отзыв (публичный эндпоинт)"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    # Валидация данных
    errors = validate_review_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    # Дополнительная проверка на спам
    if is_spam_content(data.get('text', '')):
        return jsonify({'error': 'Отзыв содержит недопустимый контент'}), 400
    
    try:
        # Создаем отзыв
        review = Review(
            name=data['name'].strip(),
            rating=int(data['rating']),
            text=data['text'].strip(),
            service_type=data.get('service_type', '').strip() if data.get('service_type') else None,
            service_id=data.get('service_id') if data.get('service_id') else None,
            avatar=data.get('avatar', '👤'),
            approved=False  # Требует модерации
            
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Отправляем уведомление администраторам (опционально)
        # send_admin_notification('new_review', review.to_dict())
        
        return jsonify({
            'message': 'Спасибо за отзыв! Он будет опубликован после модерации.',
            'review_id': review.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка создания отзыва: {e}")
        return jsonify({'error': 'Произошла ошибка при отправке отзыва'}), 500

@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Получить конкретный отзыв"""
    review = Review.query.get_or_404(review_id)
    
    # Показываем только одобренные отзывы для публичного доступа
    if not review.approved:
        return jsonify({'error': 'Отзыв не найден'}), 404
    
    return jsonify({'review': review.to_dict()})

@reviews_bp.route('/stats', methods=['GET'])
def get_review_stats():
    """Статистика отзывов"""
    total_reviews = Review.query.filter(Review.approved == True).count()
    
    # Статистика по рейтингам
    rating_stats = db.session.query(
        Review.rating,
        func.count(Review.id).label('count')
    ).filter(Review.approved == True).group_by(Review.rating).all()
    
    # Средний рейтинг
    avg_rating = db.session.query(
        func.avg(Review.rating).label('average')
    ).filter(Review.approved == True).scalar()
    
    # Последние отзывы
    recent_reviews = Review.query.filter(
        Review.approved == True
    ).order_by(desc(Review.created_at)).limit(5).all()
    
    return jsonify({
        'total_reviews': total_reviews,
        'average_rating': round(avg_rating, 1) if avg_rating else 0,
        'rating_distribution': [
            {'rating': rating, 'count': count} 
            for rating, count in rating_stats
        ],
        'recent_reviews': [review.to_dict() for review in recent_reviews]
    })

@reviews_bp.route('/by-service/<int:service_id>', methods=['GET'])
def get_reviews_by_service(service_id):
    """Получить отзывы по конкретной услуге"""
    service = Service.query.get_or_404(service_id)
    
    reviews = Review.query.filter(
        Review.service_id == service_id,
        Review.approved == True
    ).order_by(desc(Review.created_at)).all()
    
    # Статистика по этой услуге
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        rating_counts = {}
        for r in reviews:
            rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1
    else:
        avg_rating = 0
        rating_counts = {}
    
    return jsonify({
        'service': service.to_dict(),
        'reviews': [review.to_dict() for review in reviews],
        'stats': {
            'total': len(reviews),
            'average_rating': round(avg_rating, 1),
            'rating_distribution': rating_counts
        }
    })

@reviews_bp.route('/featured', methods=['GET'])
def get_featured_reviews():
    """Получить избранные отзывы (с высоким рейтингом)"""
    limit = request.args.get('limit', 6, type=int)
    
    reviews = Review.query.filter(
        Review.approved == True,
        Review.rating >= 4
    ).order_by(desc(Review.rating), desc(Review.created_at)).limit(limit).all()
    
    return jsonify({
        'reviews': [review.to_dict() for review in reviews]
    })

@reviews_bp.route('/search', methods=['GET'])
def search_reviews():
    """Поиск отзывов по тексту"""
    query_text = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query_text:
        return jsonify({'reviews': []})
    
    reviews = Review.query.filter(
        Review.approved == True,
        Review.text.contains(query_text)
    ).order_by(desc(Review.created_at)).limit(limit).all()
    
    return jsonify({
        'reviews': [review.to_dict() for review in reviews],
        'query': query_text,
        'total_found': len(reviews)
    })

@reviews_bp.route('/moderate/<int:review_id>', methods=['PUT'])
def moderate_review(review_id):
    """Модерация отзыва (только для админов)"""
    review = Review.query.get_or_404(review_id)
    data = request.get_json()
    
    action = data.get('action')  # 'approve' или 'reject'
    
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
    
    try:
        if action == 'approve':
            review.approved = True
            message = 'Отзыв одобрен'
        else:
            db.session.delete(review)
            message = 'Отзыв отклонен'
        
        db.session.commit()
        
        return jsonify({'message': message})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при модерации'}), 500

@reviews_bp.route('/pending', methods=['GET'])
def get_pending_reviews():
    """Получить отзывы, ожидающие модерации (только для админов)"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    pagination = Review.query.filter(
        Review.approved == False
    ).order_by(desc(Review.created_at)).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    reviews = [review.to_dict() for review in pagination.items]
    
    return jsonify({
        'reviews': reviews,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

def is_spam_content(text):
    """Простая проверка на спам контент"""
    spam_patterns = [
        r'https?://\S+',  # URL ссылки
        r'[а-яА-Я]*[0-9]{3,}[а-яА-Я]*',  # Много цифр подряд
        r'(.)\1{4,}',  # Повторяющиеся символы
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, text):
            return True
    
    return False


# routes/reviews.py - Дополнительные маршруты для CRUD операций с отзывами



# ... (существующие маршруты остаются без изменений)

# ============ АДМИНИСТРАТИВНЫЕ МАРШРУТЫ ============

@reviews_bp.route('/admin/reviews', methods=['GET'])
@admin_required
def get_all_reviews_admin():
    """Получить все отзывы для админки (включая неодобренные)"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status', 'all')  # 'approved', 'pending', 'all'
    rating = request.args.get('rating', type=int)
    service_type = request.args.get('service_type')
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    # Базовый запрос
    query = Review.query
    
    # Фильтр по статусу
    if status == 'approved':
        query = query.filter(Review.approved == True)
    elif status == 'pending':
        query = query.filter(Review.approved == False)
    # Для 'all' не добавляем фильтр
    
    # Другие фильтры
    if rating:
        query = query.filter(Review.rating == rating)
    
    if service_type:
        query = query.filter(Review.service_type == service_type)
    
    if search:
        search_filter = or_(
            Review.name.contains(search),
            Review.text.contains(search),
            Review.service_type.contains(search)
        )
        query = query.filter(search_filter)
    
    # Сортировка
    if hasattr(Review, sort):
        if order == 'desc':
            query = query.order_by(desc(getattr(Review, sort)))
        else:
            query = query.order_by(getattr(Review, sort))
    else:
        query = query.order_by(desc(Review.created_at))
    
    # Пагинация
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    reviews = [review.to_dict() for review in pagination.items]
    
    return jsonify({
        'reviews': reviews,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

@reviews_bp.route('/admin/reviews', methods=['POST'])
@admin_required
def create_admin_review():
    """Создать отзыв через админ-панель"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    # Валидация данных
    errors = validate_review_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        review = Review(
            name=data['name'].strip(),
            rating=int(data['rating']),
            text=data['text'].strip(),
            service_type=data.get('service_type', '').strip() if data.get('service_type') else None,
            email=data.get('email', '').strip() if data.get('email') else None,
            phone=data.get('phone', '').strip() if data.get('phone') else None,
            approved=True  # Автоматически одобряем отзывы из админки
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'message': 'Отзыв успешно создан',
            'review': review.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка создания отзыва: {e}")
        return jsonify({'error': 'Произошла ошибка при создании отзыва'}), 500

@reviews_bp.route('/admin/reviews/<int:review_id>', methods=['PUT', 'OPTIONS'])
@admin_required
def update_review(review_id):
    """Обновить отзыв"""
    if request.method == "OPTIONS":
        return '', 204  # preflight OK без редиректов
    review = Review.query.get_or_404(review_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    # Валидация данных
    errors = validate_review_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Обновляем поля
        review.name = data['name'].strip()
        review.rating = int(data['rating'])
        review.text = data['text'].strip()
        review.service_type = data.get('service_type', '').strip() if data.get('service_type') else None
        review.email = data.get('email', '').strip() if data.get('email') else None
        review.phone = data.get('phone', '').strip() if data.get('phone') else None
        review.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Отзыв успешно обновлен',
            'review': review.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка обновления отзыва: {e}")
        return jsonify({'error': 'Произошла ошибка при обновлении отзыва'}), 500

@reviews_bp.route('/admin/reviews/<int:review_id>', methods=['DELETE', 'OPTIONS'])
@admin_required
def delete_review(review_id):
    """Удалить отзыв"""
    if request.method == "OPTIONS":
        return '', 204  # preflight OK без редиректов
    review = Review.query.get_or_404(review_id)
    
    try:
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({'message': 'Отзыв успешно удален'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка удаления отзыва: {e}")
        return jsonify({'error': 'Произошла ошибка при удалении отзыва'}), 500

@reviews_bp.route('/admin/reviews/bulk-approve', methods=['POST'])
@admin_required
def bulk_approve_reviews():
    """Массовое одобрение отзывов"""
    data = request.get_json()
    review_ids = data.get('review_ids', [])
    
    if not review_ids:
        return jsonify({'error': 'Не указаны ID отзывов'}), 400
    
    try:
        updated_count = Review.query.filter(
            Review.id.in_(review_ids)
        ).update({'approved': True}, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Одобрено отзывов: {updated_count}',
            'updated_count': updated_count
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка массового одобрения: {e}")
        return jsonify({'error': 'Произошла ошибка при одобрении отзывов'}), 500

@reviews_bp.route('/admin/reviews/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_reviews():
    """Массовое удаление отзывов"""
    data = request.get_json()
    review_ids = data.get('review_ids', [])
    
    if not review_ids:
        return jsonify({'error': 'Не указаны ID отзывов'}), 400
    
    try:
        deleted_count = Review.query.filter(
            Review.id.in_(review_ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Удалено отзывов: {deleted_count}',
            'deleted_count': deleted_count
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка массового удаления: {e}")
        return jsonify({'error': 'Произошла ошибка при удалении отзывов'}), 500

@reviews_bp.route('/admin/reviews/<int:review_id>/featured', methods=['PUT'])
@admin_required
def toggle_review_featured(review_id):
    """Отметить/снять отметку избранного отзыва"""
    review = Review.query.get_or_404(review_id)
    data = request.get_json()
    
    featured = data.get('featured', True)
    
    try:
        review.featured = featured
        db.session.commit()
        
        action = 'добавлен в избранные' if featured else 'удален из избранных'
        return jsonify({
            'message': f'Отзыв {action}',
            'review': review.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка изменения статуса избранного: {e}")
        return jsonify({'error': 'Произошла ошибка при изменении статуса'}), 500

@reviews_bp.route('/admin/reviews/stats', methods=['GET'])
@admin_required
def get_admin_review_stats():
    """Детальная статистика отзывов для админки"""
    try:
        # Общая статистика
        total_reviews = Review.query.count()
        approved_reviews = Review.query.filter(Review.approved == True).count()
        pending_reviews = Review.query.filter(Review.approved == False).count()
        
        # Статистика по рейтингам
        rating_stats = db.session.query(
            Review.rating,
            func.count(Review.id).label('count')
        ).group_by(Review.rating).all()
        
        # Средний рейтинг
        avg_rating = db.session.query(
            func.avg(Review.rating).label('average')
        ).filter(Review.approved == True).scalar()
        
        # Статистика по услугам
        service_stats = db.session.query(
            Review.service_type,
            func.count(Review.id).label('count'),
            func.avg(Review.rating).label('avg_rating')
        ).filter(
            Review.approved == True,
            Review.service_type.isnot(None)
        ).group_by(Review.service_type).all()
        
        # Статистика по месяцам (последние 12 месяцев)
        monthly_stats = db.session.query(
            func.date_trunc('month', Review.created_at).label('month'),
            func.count(Review.id).label('count')
        ).filter(
            Review.created_at >= datetime.utcnow().replace(month=1, day=1)
        ).group_by(func.date_trunc('month', Review.created_at)).all()
        
        # Последние отзывы
        recent_reviews = Review.query.order_by(
            desc(Review.created_at)
        ).limit(10).all()
        
        return jsonify({
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_reviews': pending_reviews,
            'average_rating': round(avg_rating, 2) if avg_rating else 0,
            'rating_distribution': [
                {'rating': rating, 'count': count} 
                for rating, count in rating_stats
            ],
            'service_distribution': [
                {
                    'service': service_type,
                    'count': count,
                    'avg_rating': round(float(avg_rating), 2)
                }
                for service_type, count, avg_rating in service_stats
            ],
            'monthly_stats': [
                {
                    'month': month.isoformat(),
                    'count': count
                }
                for month, count in monthly_stats
            ],
            'recent_reviews': [review.to_dict() for review in recent_reviews]
        })
    
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        return jsonify({'error': 'Произошла ошибка при получении статистики'}), 500

@reviews_bp.route('/admin/reviews/export', methods=['GET'])
@admin_required
def export_reviews():
    """Экспорт отзывов в CSV"""
    try:
        # Параметры экспорта
        approved_only = request.args.get('approved_only', 'true').lower() == 'true'
        service_type = request.args.get('service_type')
        rating = request.args.get('rating', type=int)
        
        # Формируем запрос
        query = Review.query
        
        if approved_only:
            query = query.filter(Review.approved == True)
        
        if service_type:
            query = query.filter(Review.service_type == service_type)
        
        if rating:
            query = query.filter(Review.rating == rating)
        
        reviews = query.order_by(desc(Review.created_at)).all()
        
        # Создаем CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID',
            'Имя',
            'Email',
            'Телефон',
            'Услуга',
            'Рейтинг',
            'Текст отзыва',
            'Одобрен',
            'Дата создания',
            'Дата обновления'
        ])
        
        # Данные
        for review in reviews:
            writer.writerow([
                review.id,
                review.name,
                review.email or '',
                review.phone or '',
                review.service_type or '',
                review.rating,
                review.text,
                'Да' if review.approved else 'Нет',
                review.created_at.strftime('%Y-%m-%d %H:%M:%S') if review.created_at else '',
                review.updated_at.strftime('%Y-%m-%d %H:%M:%S') if review.updated_at else ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=reviews_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return jsonify({'error': 'Произошла ошибка при экспорте данных'}), 500

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def is_spam_content(text):
    """Простая проверка на спам"""
    spam_patterns = [
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'\b(?:viagra|casino|loan|credit|money)\b',
        r'[A-Z]{5,}',  # Много заглавных букв подряд
        r'(.)\1{4,}',  # Повторяющиеся символы
    ]
    
    text_lower = text.lower()
    
    for pattern in spam_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False