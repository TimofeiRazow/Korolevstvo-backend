from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from models import db, Booking, Review, Service, Portfolio

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_analytics_overview():
    """Общая аналитика"""
    # Период для анализа
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Общие метрики
    total_bookings = Booking.query.count()
    period_bookings = Booking.query.filter(Booking.created_at >= start_date).count()
    
    # Конверсия (примерная)
    total_views = period_bookings * 10  # Условно
    conversion_rate = (period_bookings / total_views * 100) if total_views > 0 else 0
    
    # Средний рейтинг
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.approved == True
    ).scalar() or 0
    
    return jsonify({
        'overview': {
            'total_bookings': total_bookings,
            'period_bookings': period_bookings,
            'total_reviews': Review.query.filter(Review.approved == True).count(),
            'average_rating': round(avg_rating, 1),
            'conversion_rate': round(conversion_rate, 2),
            'active_services': Service.query.count()
        }
    })

@analytics_bp.route('/bookings-trend', methods=['GET'])
@jwt_required()
def get_bookings_trend():
    """Тренд заявок по дням/месяцам"""
    period = request.args.get('period', 'month')  # day, week, month
    
    if period == 'day':
        # По дням за последний месяц
        date_format = '%Y-%m-%d'
        start_date = datetime.utcnow() - timedelta(days=30)
    elif period == 'week':
        # По неделям за последние 3 месяца
        date_format = '%Y-%W'
        start_date = datetime.utcnow() - timedelta(weeks=12)
    else:  # month
        # По месяцам за последний год
        date_format = '%Y-%m'
        start_date = datetime.utcnow() - timedelta(days=365)
    
    trend_data = db.session.query(
        func.strftime(date_format, Booking.created_at).label('period'),
        func.count(Booking.id).label('count')
    ).filter(
        Booking.created_at >= start_date
    ).group_by(
        func.strftime(date_format, Booking.created_at)
    ).order_by('period').all()
    
    return jsonify({
        'trend_data': [
            {'period': period, 'count': count}
            for period, count in trend_data
        ]
    })

@analytics_bp.route('/popular-services', methods=['GET'])
@jwt_required()
def get_popular_services():
    """Популярные услуги"""
    limit = request.args.get('limit', 10, type=int)
    
    popular_services = db.session.query(
        Service.title,
        Service.category,
        func.count(Booking.id).label('bookings_count')
    ).outerjoin(Booking).group_by(Service.id).order_by(
        func.count(Booking.id).desc()
    ).limit(limit).all()
    
    return jsonify({
        'popular_services': [
            {
                'title': title,
                'category': category,
                'bookings_count': count
            }
            for title, category, count in popular_services
        ]
    })

@analytics_bp.route('/revenue-estimate', methods=['GET'])
@jwt_required()
def get_revenue_estimate():
    """Оценка доходов (примерная)"""
    # Примерные цены по категориям
    category_prices = {
        'children': 50000,
        'weddings': 300000,
        'corporate': 150000,
        'anniversaries': 100000,
        'shows': 80000,
        'animators': 25000
    }
    
    revenue_by_category = []
    total_revenue = 0
    
    for category, avg_price in category_prices.items():
        bookings_count = db.session.query(func.count(Booking.id)).join(Service).filter(
            Service.category == category,
            Booking.status == 'completed'
        ).scalar()
        
        category_revenue = bookings_count * avg_price
        total_revenue += category_revenue
        
        revenue_by_category.append({
            'category': category,
            'bookings_count': bookings_count,
            'estimated_revenue': category_revenue
        })
    
    return jsonify({
        'revenue_by_category': revenue_by_category,
        'total_estimated_revenue': total_revenue
    })

@analytics_bp.route('/customer-satisfaction', methods=['GET'])
@jwt_required()
def get_customer_satisfaction():
    """Удовлетворенность клиентов"""
    # Распределение оценок
    rating_distribution = db.session.query(
        Review.rating,
        func.count(Review.id).label('count')
    ).filter(Review.approved == True).group_by(Review.rating).all()
    
    # NPS (Net Promoter Score) - упрощенный расчет
    total_reviews = sum(count for _, count in rating_distribution)
    promoters = sum(count for rating, count in rating_distribution if rating >= 4)
    detractors = sum(count for rating, count in rating_distribution if rating <= 2)
    
    nps = ((promoters - detractors) / total_reviews * 100) if total_reviews > 0 else 0
    
    return jsonify({
        'rating_distribution': [
            {'rating': rating, 'count': count}
            for rating, count in rating_distribution
        ],
        'nps_score': round(nps, 1),
        'total_reviews': total_reviews,
        'promoters': promoters,
        'detractors': detractors
    })

@analytics_bp.route('/booking-sources', methods=['GET'])
@jwt_required()
def get_booking_sources():
    """Источники заявок (mock data)"""
    # В реальном приложении эти данные собираются через UTM метки
    mock_sources = [
        {'source': 'Прямые заходы', 'count': 45, 'percentage': 35},
        {'source': 'Instagram', 'count': 30, 'percentage': 23},
        {'source': 'Google поиск', 'count': 25, 'percentage': 19},
        {'source': 'Рекомендации', 'count': 20, 'percentage': 15},
        {'source': 'Facebook', 'count': 10, 'percentage': 8}
    ]
    
    return jsonify({
        'booking_sources': mock_sources
    })