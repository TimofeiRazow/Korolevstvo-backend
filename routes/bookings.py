# routes/bookings.py - ИСПРАВЛЕННАЯ версия с правильным использованием Telegram

from flask import Blueprint, request, jsonify
from datetime import datetime, date, time
from models import db, Booking, Service
from utils.validators import validate_booking_data
from utils.email_utils import send_booking_notification as send_email_notification
import asyncio
# ПРАВИЛЬНЫЙ ИМПОРТ
from utils.helpers import generate_booking_number

from utils.telegram_integration import send_telegram_booking_notification, is_telegram_notifications_enabled
TELEGRAM_AVAILABLE = True


bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/', methods=['POST'])
def create_booking():
    """Создать новую заявку на бронирование"""
    data = request.get_json()
    
    # Валидация данных
    errors = validate_booking_data(data)
    print(errors)
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
        
        print(f"\n🎉 === НОВАЯ ЗАЯВКА СОЗДАНА ===")
        print(f"📋 ID: #{booking.id}")
        print(f"👤 Имя: {booking.name}")
        print(f"📞 Телефон: {booking.phone}")
        print(f"🎪 Услуга: {booking.service.title if booking.service else 'Не указана'}")
        
        # Отправка email уведомлений
        email_sent = False
        email_error = None
        try:
            print("📧 Отправляем email...")
            send_email_notification(booking)
            email_sent = True
            print("✅ Email отправлен")
        except Exception as e:
            email_error = str(e)
            print(f"❌ Email ошибка: {e}")
        
        # Проверка и отправка Telegram уведомлений
        telegram_sent = False
        telegram_error = None
        telegram_status = {}
        
        if TELEGRAM_AVAILABLE:
            try:
                # Проверяем все настройки Telegram
                from utils.telegram_integration import validate_telegram_settings
                telegram_status = validate_telegram_settings()
                print(telegram_status)
                print(f"📱 Проверка Telegram настроек:")
                print(f"   - Уведомления включены: {telegram_status['notifications_enabled']}")
                print(f"   - Chat ID настроен: {telegram_status['chat_id_configured']}")
                print(f"   - Chat ID: {telegram_status.get('chat_id', 'Не настроен')}")
                print(f"   - Сервис доступен: {telegram_status['service_available']}")
                print(f"   - Готов к работе: {telegram_status['ready']}")
                
                asyncio.run(send_telegram_booking_notification(booking))
 
                
            except Exception as e:
                telegram_error = str(e)
                print(f"❌ Telegram ошибка: {e}")
        else:
            telegram_error = "Telegram интеграция недоступна"
            print("⚠️ Telegram интеграция недоступнащшщшщшшщщ")
        
        print(f"🏁 === ЗАЯВКА #{booking.id} ОБРАБОТАНА ===\n")
        
        return jsonify({
            'booking': booking.to_dict(),
            'message': 'Заявка успешно создана!'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"💥 Ошибка создания заявки: {e}")
        return jsonify({'error': 'Ошибка при создании заявки'}), 500
    
    
@bookings_bp.route('/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """Обновить заявку с отправкой уведомлений при изменении статуса"""
    print(f"\n🔄 === ОБНОВЛЕНИЕ ЗАЯВКИ #{booking_id} ===")
    
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()
    
    print(f"📋 Текущая заявка:")
    print(f"   ID: {booking.id}")
    print(f"   Имя: {booking.name}")
    print(f"   Телефон: {booking.phone}")
    print(f"   Старый статус: {booking.status}")
    
    print(f"📥 Полученные данные: {data}")
    
    try:
        old_status = booking.status
        
        # Обновление полей
        if 'status' in data:
            booking.status = data['status']
            print(f"🔄 Статус изменен: {old_status} → {booking.status}")
        else:
            print("⚠️ Поле 'status' отсутствует в данных")
            
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
        print("✅ Изменения сохранены в БД")
        
        # Проверяем условия для отправки уведомления
        status_changed = old_status != booking.status
        is_notifiable_status = booking.status in ['confirmed', 'in-progress', 'completed', 'cancelled']
    
        
        print(f"🏁 === ЗАВЕРШЕНИЕ ОБНОВЛЕНИЯ #{booking_id} ===\n")
        
        return jsonify({
            'booking': booking.to_dict(),
            'message': 'Заявка обновлена!',
            'debug': {
                'old_status': old_status,
                'new_status': booking.status,
                'status_changed': status_changed,
                'notification_conditions_met': status_changed and is_notifiable_status and bool(booking.phone)
            }
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА при обновлении заявки: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка при обновлении заявки'}), 500

@bookings_bp.route('/quick-request', methods=['POST'])
def quick_request():
    """Быстрая заявка (минимум данных) с Telegram уведомлением"""
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
        
        return jsonify({
            'booking_id': booking.id,
            'message': 'Заявка принята! Мы перезвоним в течение 15 минут.'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"💥 Ошибка создания быстрой заявки: {e}")
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

# Остальные маршруты без изменений...

@bookings_bp.route('/', methods=['GET'])
def get_all_bookings():
    """Получить все заявки с фильтрацией, пагинацией и сортировкой"""
    try:
        # Параметры пагинации
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        # Параметры фильтрации
        status = request.args.get('status')
        service_id = request.args.get('service_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search')
        
        # Параметры сортировки
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Базовый запрос
        query = Booking.query
        
        # Применяем фильтры
        if status:
            query = query.filter(Booking.status == status)
        
        if service_id:
            query = query.filter(Booking.service_id == service_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(Booking.event_date >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Неверный формат даты date_from. Используйте YYYY-MM-DD'}), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(Booking.event_date <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'Неверный формат даты date_to. Используйте YYYY-MM-DD'}), 400
        
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    Booking.name.ilike(search_pattern),
                    Booking.phone.ilike(search_pattern),
                    Booking.email.ilike(search_pattern)
                )
            )
        
        # Применяем сортировку
        valid_sort_fields = ['id', 'name', 'phone', 'event_date', 'event_time', 'status', 'created_at', 'updated_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        sort_column = getattr(Booking, sort_by)
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Выполняем пагинацию
        paginated_bookings = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Формируем ответ
        bookings_data = []
        for booking in paginated_bookings.items:
            booking_dict = booking.to_dict()
            bookings_data.append(booking_dict)
        
        # Статистика по статусам
        stats = db.session.query(
            Booking.status,
            db.func.count(Booking.id).label('count')
        ).group_by(Booking.status).all()
        
        status_stats = {stat.status: stat.count for stat in stats}
        
        return jsonify({
            'bookings': bookings_data,
            'pagination': {
                'page': paginated_bookings.page,
                'pages': paginated_bookings.pages,
                'per_page': paginated_bookings.per_page,
                'total': paginated_bookings.total,
                'has_next': paginated_bookings.has_next,
                'has_prev': paginated_bookings.has_prev,
                'next_num': paginated_bookings.next_num,
                'prev_num': paginated_bookings.prev_num
            },
            'filters': {
                'status': status,
                'service_id': service_id,
                'date_from': date_from,
                'date_to': date_to,
                'search': search,
                'sort_by': sort_by,
                'sort_order': sort_order
            },
            'stats': {
                'total_bookings': paginated_bookings.total,
                'status_breakdown': status_stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Ошибка при получении заявок',
            'details': str(e)
        }), 500

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Получить заявку по ID"""
    booking = Booking.query.get_or_404(booking_id)
    return jsonify({'booking': booking.to_dict()})

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

# Дополнительный маршрут для отладки Telegram
@bookings_bp.route('/debug/telegram/<phone>', methods=['GET'])
def debug_telegram_user(phone):
    """Отладочный маршрут для проверки пользователя Telegram"""
    try:
        from utils.telegram_bot import debug_check_user
        user = debug_check_user(phone)
        
        if user:
            return jsonify({
                'found': True,
                'user': {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'is_verified': user.is_verified,
                    'created_at': user.created_at.isoformat(),
                    'last_activity': user.last_activity.isoformat() if user.last_activity else None
                }
            })
        else:
            return jsonify({
                'found': False,
                'message': f'Пользователь с телефоном {phone} не найден'
            })
    
    except Exception as e:
        return jsonify({
            'error': 'Ошибка при проверке пользователя',
            'details': str(e)
        }), 500

# Тестовый маршрут для Telegram
@bookings_bp.route('/test/telegram/<phone>', methods=['POST'])
def test_telegram_notification(phone):
    """Тестовая отправка Telegram уведомления"""
    try:
        from utils.telegram_bot import send_telegram_message, debug_check_user
        
        # Проверяем пользователя
        user = debug_check_user(phone)
        if not user:
            return jsonify({'error': f'Пользователь с телефоном {phone} не найден'}), 404
        
        if not user.is_verified:
            return jsonify({'error': 'Пользователь не верифицирован'}), 400
        
        # Отправляем тестовое сообщение
        test_message = f"""🧪 <b>Тестовое уведомление</b>

Привет, {user.first_name}! 

Это тест системы уведомлений Королевства Чудес.

Если вы получили это сообщение, значит всё работает! ✅

⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"""

        result = send_telegram_message(user.telegram_id, test_message)
        
        return jsonify({
            'success': result,
            'message': 'Тестовое сообщение отправлено' if result else 'Ошибка отправки',
            'user': user.get_display_name(),
            'telegram_id': user.telegram_id
        })
    
    except Exception as e:
        return jsonify({
            'error': 'Ошибка при тестировании',
            'details': str(e)
        }), 500