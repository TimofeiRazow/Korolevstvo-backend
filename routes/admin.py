from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from models import db, Booking, Review, Service, Portfolio
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)

# Простая аутентификация (в продакшене использовать настоящую БД пользователей)
ADMIN_CREDENTIALS = {
    'admin': 'admin123',  # В продакшене должны быть хешированы
    'manager': 'manager123'
}

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Вход в админ панель"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
        access_token = create_access_token(
            identity=username,
            expires_delta=timedelta(hours=8)
        )
        return jsonify({
            'access_token': access_token,
            'username': username,
            'message': 'Вход выполнен успешно'
        })
    
    return jsonify({'error': 'Неверные учетные данные'}), 401

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    
    """Получить данные дашборда"""
    # Статистика за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    stats = {
        'bookings': {
            'total': Booking.query.count(),
            'new': Booking.query.filter(Booking.status == 'new').count(),
            'confirmed': Booking.query.filter(Booking.status == 'confirmed').count(),
            'this_month': Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
        },
        'reviews': {
            'total': Review.query.count(),
            'pending': Review.query.filter(Review.approved == False).count(),
            'average_rating': db.session.query(func.avg(Review.rating)).filter(Review.approved == True).scalar() or 0
        },
        'services': {
            'total': Service.query.count(),
            'featured': Service.query.filter(Service.featured == True).count()
        }
    }
    
    # Последние заявки
    recent_bookings = Booking.query.order_by(desc(Booking.created_at)).limit(10).all()
    
    # Отзывы на модерацию
    pending_reviews = Review.query.filter(Review.approved == False).limit(5).all()

    return jsonify({
        'stats': stats,
        'recent_bookings': [booking.to_dict() for booking in recent_bookings],
        'pending_reviews': [review.to_dict() for review in pending_reviews]
    })


@admin_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_admin_bookings():
    """Получить все заявки для админа"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    
    query = Booking.query
    
    if status:
        query = query.filter(Booking.status == status)
    
    query = query.order_by(desc(Booking.created_at))
    
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'bookings': [booking.to_dict() for booking in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })

@admin_bp.route('/bookings/<int:booking_id>', methods=['PUT'])
@jwt_required()
def update_booking_status(booking_id):
    """Обновить статус заявки"""
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()
    
    new_status = data.get('status')
    if new_status not in ['new', 'confirmed', 'cancelled', 'completed']:
        return jsonify({'error': 'Неверный статус'}), 400
    
    try:
        booking.status = new_status
        db.session.commit()
        
        return jsonify({
            'booking': booking.to_dict(),
            'message': f'Статус изменен на {new_status}'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при обновлении'}), 500

@admin_bp.route('/reviews', methods=['GET'])
@jwt_required()
def get_admin_reviews():
    """Получить отзывы для модерации"""
    pending_only = request.args.get('pending_only', False, type=bool)
    
    query = Review.query
    
    if pending_only:
        query = query.filter(Review.approved == False)
    
    reviews = query.order_by(desc(Review.created_at)).all()
    
    return jsonify({
        'reviews': [review.to_dict() for review in reviews]
    })

@admin_bp.route('/reviews/<int:review_id>/approve', methods=['PUT'])
@jwt_required()
def approve_review(review_id):
    """Одобрить отзыв"""
    review = Review.query.get_or_404(review_id)
    
    try:
        review.approved = True
        db.session.commit()
        
        return jsonify({
            'message': 'Отзыв одобрен',
            'review': review.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при одобрении'}), 500

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Получить аналитику"""
    # Статистика по месяцам
    monthly_bookings = db.session.query(
        func.strftime('%Y-%m', Booking.created_at).label('month'),
        func.count(Booking.id).label('count')
    ).group_by(func.strftime('%Y-%m', Booking.created_at)).limit(12).all()
    
    # Популярные услуги
    popular_services = db.session.query(
        Service.title,
        func.count(Booking.id).label('bookings_count')
    ).join(Booking).group_by(Service.id).order_by(
        func.count(Booking.id).desc()
    ).limit(10).all()
    
    # Статистика по статусам
    status_stats = db.session.query(
        Booking.status,
        func.count(Booking.id).label('count')
    ).group_by(Booking.status).all()
    
    return jsonify({
        'monthly_bookings': [
            {'month': month, 'count': count} 
            for month, count in monthly_bookings
        ],
        'popular_services': [
            {'service': title, 'bookings': count} 
            for title, count in popular_services
        ],
        'status_distribution': [
            {'status': status, 'count': count} 
            for status, count in status_stats
        ]
    })