from flask import Blueprint, request, jsonify
from sqlalchemy import desc, func
from models import db, Review, Service
from utils.validators import validate_review_data

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/', methods=['GET'])
def get_reviews():
    """Получить список отзывов с фильтрацией и пагинацией"""
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

@reviews_bp.route('/', methods=['POST'])
def create_review():
    """Добавить новый отзыв"""
    data = request.get_json()
    
    # Валидация данных
    errors = validate_review_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        review = Review(
            name=data['name'],
            rating=data['rating'],
            text=data['text'],
            service_type=data.get('service_type'),
            service_id=data.get('service_id'),
            avatar=data.get('avatar', '👤'),
            approved=False  # Требует модерации
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'review': review.to_dict(),
            'message': 'Отзыв отправлен на модерацию. Спасибо!'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при добавлении отзыва'}), 500

@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Получить конкретный отзыв"""
    review = Review.query.get_or_404(review_id)
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