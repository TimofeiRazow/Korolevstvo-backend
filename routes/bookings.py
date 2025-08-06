from flask import Blueprint, request, jsonify
from datetime import datetime, date, time
from models import db, Booking, Service
from utils.validators import validate_booking_data
from utils.email import send_booking_notification
from utils.helpers import generate_booking_number

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/', methods=['POST'])
def create_booking():
    """Создать новую заявку на бронирование"""
    data = request.get_json()
    
    # Валидация данных
    errors = validate_booking_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Создание новой заявки
        booking = Booking(
            name=data['name'],
            phone=data['phone'],
            email=data.get('email'),
            service_id=data.get('service_id'),
            event_date=datetime.strptime(data['event_date'], '%Y-%m-%d').date() if data.get('event_date') else None,
            event_time=datetime.strptime(data['event_time'], '%H:%M').time() if data.get('event_time') else None,
            guests_count=data.get('guests_count'),
            budget=data.get('budget'),
            location=data.get('location'),
            message=data.get('message', ''),
            status='new'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Отправка уведомлений
        try:
            send_booking_notification(booking)
        except Exception as e:
            print(f"Email notification failed: {e}")
        
        return jsonify({
            'booking': booking.to_dict(),
            'message': 'Заявка успешно создана!'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Получить заявку по ID"""
    booking = Booking.query.get_or_404(booking_id)
    return jsonify({'booking': booking.to_dict()})

@bookings_bp.route('/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """Обновить заявку"""
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()
    
    try:
        # Обновление полей
        if 'status' in data:
            booking.status = data['status']
        if 'event_date' in data and data['event_date']:
            booking.event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
        if 'event_time' in data and data['event_time']:
            booking.event_time = datetime.strptime(data['event_time'], '%H:%M').time()
        if 'guests_count' in data:
            booking.guests_count = data['guests_count']
        if 'location' in data:
            booking.location = data['location']
        if 'message' in data:
            booking.message = data['message']
        
        db.session.commit()
        
        return jsonify({
            'booking': booking.to_dict(),
            'message': 'Заявка обновлена!'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при обновлении заявки'}), 500

@bookings_bp.route('/check-availability', methods=['GET'])
def check_availability():
    """Проверить доступность даты"""
    event_date = request.args.get('date')
    service_id = request.args.get('service_id', type=int)
    
    if not event_date:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    try:
        check_date = datetime.strptime(event_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Проверяем занятые слоты на эту дату
    query = Booking.query.filter(
        Booking.event_date == check_date,
        Booking.status.in_(['confirmed', 'new'])
    )
    
    if service_id:
        query = query.filter(Booking.service_id == service_id)
    
    bookings = query.all()
    
    # Определяем доступные временные слоты
    all_slots = [
        '10:00', '11:00', '12:00', '13:00', '14:00', 
        '15:00', '16:00', '17:00', '18:00', '19:00'
    ]
    
    booked_slots = [booking.event_time.strftime('%H:%M') for booking in bookings if booking.event_time]
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    
    return jsonify({
        'date': event_date,
        'available': len(available_slots) > 0,
        'available_slots': available_slots,
        'booked_slots': booked_slots,
        'total_bookings': len(bookings)
    })

@bookings_bp.route('/quick-request', methods=['POST'])
def quick_request():
    """Быстрая заявка (минимум данных)"""
    data = request.get_json()
    
    if not data.get('phone'):
        return jsonify({'error': 'Номер телефона обязателен'}), 400
    
    try:
        booking = Booking(
            name=data.get('name', 'Не указано'),
            phone=data['phone'],
            message=data.get('message', 'Быстрая заявка - перезвоните пожалуйста'),
            status='new'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Отправка уведомления
        try:
            send_booking_notification(booking, is_quick=True)
        except Exception as e:
            print(f"Email notification failed: {e}")
        
        return jsonify({
            'booking_id': booking.id,
            'message': 'Заявка принята! Мы перезвоним в течение 15 минут.'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

@bookings_bp.route('/callback', methods=['POST'])
def request_callback():
    """Заказать обратный звонок"""
    data = request.get_json()
    
    if not data.get('phone'):
        return jsonify({'error': 'Номер телефона обязателен'}), 400
    
    try:
        booking = Booking(
            name=data.get('name', 'Заказ обратного звонка'),
            phone=data['phone'],
            message=f"Обратный звонок. Удобное время: {data.get('preferred_time', 'любое время')}",
            status='callback_requested'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'message': 'Заявка на обратный звонок принята!'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

@bookings_bp.route('/stats', methods=['GET'])
def booking_stats():
    """Статистика заявок"""
    from sqlalchemy import func
    
    total_bookings = Booking.query.count()
    
    status_stats = db.session.query(
        Booking.status,
        func.count(Booking.id).label('count')
    ).group_by(Booking.status).all()
    
    # Статистика по месяцам
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', Booking.created_at).label('month'),
        func.count(Booking.id).label('count')
    ).group_by(func.strftime('%Y-%m', Booking.created_at)).limit(12).all()
    
    # Популярные услуги
    service_stats = db.session.query(
        Service.title,
        func.count(Booking.id).label('bookings_count')
    ).join(Booking).group_by(Service.id).order_by(
        func.count(Booking.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'total_bookings': total_bookings,
        'status_stats': [{'status': status, 'count': count} for status, count in status_stats],
        'monthly_stats': [{'month': month, 'count': count} for month, count in monthly_stats],
        'popular_services': [{'service': title, 'bookings': count} for title, count in service_stats]
    })