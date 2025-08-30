# routes/bookings.py - ОБНОВЛЕННАЯ версия с автоматическим управлением лидами

from flask import Blueprint, request, jsonify
from datetime import datetime, date, time
from models import db, Booking, Service, Lead
from utils.validators import validate_booking_data
from utils.email_utils import send_booking_notification as send_email_notification
import asyncio
from utils.helpers import generate_booking_number
from utils.telegram_integration import send_telegram_booking_notification, is_telegram_notifications_enabled

TELEGRAM_AVAILABLE = True

bookings_bp = Blueprint('bookings', __name__)

def find_or_create_lead_from_booking(booking_data):
    """
    Найти существующий лид по телефону или создать новый на основе данных заявки
    """
    phone = booking_data.get('phone')
    if not phone:
        return None
    
    try:
        # Ищем существующий лид по телефону
        existing_lead = Lead.find_by_phone(phone)
        
        if existing_lead:
            print(f"📋 Найден существующий лид #{existing_lead.id} для телефона {phone}")
            
            # Обновляем информацию в лиде, если она отсутствует
            updated = False
            if not existing_lead.email and booking_data.get('email'):
                existing_lead.email = booking_data['email']
                updated = True
            
            if not existing_lead.preferred_date and booking_data.get('event_date'):
                try:
                    existing_lead.preferred_date = datetime.strptime(booking_data['event_date'], '%Y-%m-%d').date()
                    updated = True
                except:
                    pass
            
            if not existing_lead.guests_count and booking_data.get('guests_count'):
                existing_lead.guests_count = booking_data['guests_count']
                updated = True
            
            if not existing_lead.location_preference and booking_data.get('location'):
                existing_lead.location_preference = booking_data['location']
                updated = True
            
            if not existing_lead.preferred_budget and booking_data.get('budget'):
                existing_lead.preferred_budget = booking_data['budget']
                updated = True
            
            # Определяем тип события на основе услуги
            if not existing_lead.event_type and booking_data.get('service_title'):
                service_title = booking_data['service_title'].lower()
                if 'детск' in service_title or 'день рождения' in service_title:
                    existing_lead.event_type = 'birthday'
                elif 'свадьб' in service_title:
                    existing_lead.event_type = 'wedding'
                elif 'корпорат' in service_title:
                    existing_lead.event_type = 'corporate'
                updated = True
            
            # Обновляем температуру лида (повторная заявка = горячий лид)
            if existing_lead.temperature == 'cold':
                existing_lead.temperature = 'warm'
                updated = True
            
            # Обновляем статус, если лид еще не конвертирован
            if existing_lead.status not in ['converted'] and existing_lead.status in ['new', 'contacted']:
                existing_lead.status = 'interested'
                updated = True
            
            if updated:
                existing_lead.updated_at = datetime.utcnow()
                existing_lead.calculate_quality_score()
                print(f"✅ Обновлен лид #{existing_lead.id}")
            
            return existing_lead
        
        else:
            # Создаем новый лид на основе данных заявки
            print(f"🆕 Создаем новый лид для телефона {phone}")
            
            lead_data = {
                'name': booking_data.get('name', 'Не указано'),
                'phone': phone,
                'email': booking_data.get('email'),
                'source': 'website',  # По умолчанию, если не указано иначе
                'status': 'new',
                'temperature': 'warm',  # Заявка = теплый лид
                'preferred_contact_method': 'phone',
                'guests_count': booking_data.get('guests_count'),
                'location_preference': booking_data.get('location'),
                'preferred_budget': booking_data.get('budget'),
                'notes': f"Автоматически создан из заявки. Сообщение: {booking_data.get('message', '')}"
            }
            
            # Определяем тип события
            if booking_data.get('service_title'):
                service_title = booking_data['service_title'].lower()
                if 'детск' in service_title or 'день рождения' in service_title:
                    lead_data['event_type'] = 'birthday'
                elif 'свадьб' in service_title:
                    lead_data['event_type'] = 'wedding'
                elif 'корпорат' in service_title:
                    lead_data['event_type'] = 'corporate'
                else:
                    lead_data['event_type'] = 'other'
            
            # Устанавливаем предпочитаемую дату
            if booking_data.get('event_date'):
                try:
                    lead_data['preferred_date'] = datetime.strptime(booking_data['event_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Создаем лид
            new_lead = Lead()
            new_lead.update_from_dict(lead_data)
            new_lead.calculate_quality_score()
            
            db.session.add(new_lead)
            db.session.flush()  # Получаем ID
            
            print(f"✅ Создан новый лид #{new_lead.id} для {new_lead.name}")
            return new_lead
    
    except Exception as e:
        print(f"❌ Ошибка при работе с лидом: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_lead_on_booking_status_change(booking, old_status, new_status):
    """
    Обновить лид при изменении статуса заявки
    """
    try:
        # Находим или создаем лид для этой заявки
        lead = None
        
        # Если у заявки уже есть связанный лид
        if hasattr(booking, 'source_lead') and booking.source_lead:
            lead = booking.source_lead
        else:
            # Ищем лид по телефону
            lead = Lead.find_by_phone(booking.phone)
            
            # Если лид не найден, создаем новый
            if not lead:
                booking_data = {
                    'name': booking.name,
                    'phone': booking.phone,
                    'email': booking.email,
                    'service_title': booking.service_title,
                    'event_date': booking.event_date.strftime('%Y-%m-%d') if booking.event_date else None,
                    'guests_count': booking.guests_count,
                    'location': booking.location,
                    'budget': booking.budget,
                    'message': booking.message
                }
                lead = find_or_create_lead_from_booking(booking_data)
                
                # Связываем заявку с лидом
                if lead and hasattr(booking, 'lead_id'):
                    booking.lead_id = lead.id
        
        if not lead:
            print(f"⚠️ Не удалось найти или создать лид для заявки #{booking.id}")
            return
        
        # Обновляем лид в зависимости от статуса заявки
        lead_updated = False
        
        if new_status == 'confirmed':
            if lead.status not in ['converted']:
                lead.status = 'qualified'
                lead.temperature = 'hot'
                lead_updated = True
                print(f"🔥 Лид #{lead.id} переведен в статус 'qualified' (заявка подтверждена)")
        
        elif new_status == 'in-progress':
            if lead.status not in ['converted']:
                lead.status = 'qualified'
                lead.temperature = 'hot'
                lead_updated = True
                print(f"🚀 Лид #{lead.id} в работе")
        
        elif new_status == 'completed':
            if lead.status != 'converted':
                lead.status = 'converted'
                lead.converted_at = datetime.utcnow()
                lead_updated = True
                print(f"🎉 Лид #{lead.id} конвертирован (заявка выполнена)")
        
        elif new_status == 'cancelled':
            if lead.status not in ['converted', 'lost']:
                # Проверяем, есть ли другие активные заявки у этого лида
                other_active_bookings = Booking.query.filter(
                    Booking.phone == booking.phone,
                    Booking.id != booking.id,
                    Booking.status.in_(['new', 'confirmed', 'in-progress'])
                ).count()
                
                if other_active_bookings == 0:
                    lead.status = 'lost'
                    lead.temperature = 'cold'
                    lead_updated = True
                    print(f"❄️ Лид #{lead.id} переведен в статус 'lost' (заявка отменена)")
                else:
                    print(f"📋 Лид #{lead.id} имеет другие активные заявки, статус не изменен")
        
        # Обновляем информацию о последнем контакте
        if new_status in ['confirmed', 'in-progress', 'completed']:
            lead.last_contact_date = datetime.utcnow()
            lead_updated = True
        
        # Сохраняем изменения
        if lead_updated:
            lead.updated_at = datetime.utcnow()
            lead.calculate_quality_score()
            print(f"✅ Лид #{lead.id} обновлен")
    
    except Exception as e:
        print(f"❌ Ошибка при обновлении лида: {e}")
        import traceback
        traceback.print_exc()

@bookings_bp.route('/', methods=['POST'])
def create_booking():
    """Создать новую заявку на бронирование с автоматическим управлением лидом"""
    data = request.get_json()
    
    # Валидация данных
    errors = validate_booking_data(data)
    print(errors)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # 🆕 НОВОЕ: Найти или создать лид ПЕРЕД созданием заявки
        lead = find_or_create_lead_from_booking(data)
        
        # Создание новой заявки
        print(data.get('service_title'))
        booking = Booking(
            name=data['name'],
            phone=data['phone'],
            email=data.get('email'),
            service_id=data.get('service_id'),
            service_title=data.get('service_title'),
            event_date=datetime.strptime(data['event_date'], '%Y-%m-%d').date() if data.get('event_date') else None,
            event_time=datetime.strptime(data['event_time'], '%H:%M').time() if data.get('event_time') else None,
            guests_count=data.get('guests_count'),
            budget=data.get('budget'),
            location=data.get('location'),
            message=data.get('message', ''),
            status='new'
        )
        
        # 🆕 НОВОЕ: Связываем заявку с лидом
        if lead and hasattr(booking, 'lead_id'):
            booking.lead_id = lead.id
            print(f"🔗 Заявка связана с лидом #{lead.id}")
        
        db.session.add(booking)
        db.session.commit()
        
        print(f"\n🎉 === НОВАЯ ЗАЯВКА СОЗДАНА ===")
        print(f"📋 ID: #{booking.id}")
        print(f"👤 Имя: {booking.name}")
        print(f"📞 Телефон: {booking.phone}")
        print(f"🎪 Услуга: {booking.service_title if booking.service else 'Не указана'}")
        if lead:
            print(f"🎯 Связанный лид: #{lead.id} (статус: {lead.status})")
        
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
            print("⚠️ Telegram интеграция недоступна")
        
        print(f"🏁 === ЗАЯВКА #{booking.id} ОБРАБОТАНА ===\n")
        
        # Формируем ответ с информацией о лиде
        response_data = {
            'booking': booking.to_dict(),
            'message': 'Заявка успешно создана!'
        }
        
        if lead:
            response_data['lead'] = {
                'id': lead.id,
                'status': lead.status,
                'quality_score': lead.quality_score,
                'temperature': lead.temperature
            }
        
        return jsonify(response_data), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"💥 Ошибка создания заявки: {e}")
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

@bookings_bp.route('/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """Обновить заявку с автоматическим управлением лидом при изменении статуса"""
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
        
        # 🆕 НОВОЕ: Автоматическое управление лидом при изменении статуса
        status_changed = old_status != booking.status
        if status_changed:
            print(f"🎯 Статус заявки изменился, обновляем связанный лид...")
            update_lead_on_booking_status_change(booking, old_status, booking.status)
        
        # Проверяем условия для отправки уведомления
        is_notifiable_status = booking.status in ['confirmed', 'in-progress', 'completed', 'cancelled']
        
        print(f"🏁 === ЗАВЕРШЕНИЕ ОБНОВЛЕНИЯ #{booking_id} ===\n")
        
        return jsonify({
            'booking': booking.to_dict(),
            'message': 'Заявка обновлена!',
            'debug': {
                'old_status': old_status,
                'new_status': booking.status,
                'status_changed': status_changed,
                'notification_conditions_met': status_changed and is_notifiable_status and bool(booking.phone),
                'lead_updated': status_changed
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
    """Быстрая заявка с автоматическим созданием лида"""
    data = request.get_json()
    
    if not data.get('phone'):
        return jsonify({'error': 'Номер телефона обязателен'}), 400
    
    try:
        # 🆕 НОВОЕ: Найти или создать лид для быстрой заявки
        lead_data = {
            'name': data.get('name', 'Не указано'),
            'phone': data['phone'],
            'message': data.get('message', 'Быстрая заявка - перезвоните пожалуйста')
        }
        lead = find_or_create_lead_from_booking(lead_data)
        
        booking = Booking(
            name=data.get('name', 'Не указано'),
            phone=data['phone'],
            message=data.get('message', 'Быстрая заявка - перезвоните пожалуйста'),
            status='new'
        )
        
        # Связываем с лидом
        if lead and hasattr(booking, 'lead_id'):
            booking.lead_id = lead.id
        
        db.session.add(booking)
        db.session.commit()
        
        response_data = {
            'booking_id': booking.id,
            'message': 'Заявка принята! Мы перезвоним в течение 15 минут.'
        }
        
        if lead:
            response_data['lead_id'] = lead.id
        
        return jsonify(response_data), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"💥 Ошибка создания быстрой заявки: {e}")
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

# Остальные маршруты остаются без изменений...

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
            
            # 🆕 НОВОЕ: Добавляем информацию о связанном лиде
            if hasattr(booking, 'source_lead') and booking.source_lead:
                booking_dict['lead'] = {
                    'id': booking.source_lead.id,
                    'status': booking.source_lead.status,
                    'quality_score': booking.source_lead.quality_score,
                    'temperature': booking.source_lead.temperature
                }
            elif hasattr(booking, 'lead_id') and booking.lead_id:
                # Ленивая загрузка лида, если есть lead_id
                lead = Lead.query.get(booking.lead_id)
                if lead:
                    booking_dict['lead'] = {
                        'id': lead.id,
                        'status': lead.status,
                        'quality_score': lead.quality_score,
                        'temperature': lead.temperature
                    }
            
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
    """Получить заявку по ID с информацией о связанном лиде"""
    booking = Booking.query.get_or_404(booking_id)
    booking_dict = booking.to_dict()
    
    # 🆕 НОВОЕ: Добавляем информацию о связанном лиде
    if hasattr(booking, 'source_lead') and booking.source_lead:
        booking_dict['lead'] = booking.source_lead.to_dict(include_personal=True)
    elif hasattr(booking, 'lead_id') and booking.lead_id:
        lead = Lead.query.get(booking.lead_id)
        if lead:
            booking_dict['lead'] = lead.to_dict(include_personal=True)
    
    return jsonify({'booking': booking_dict})

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

# 🆕 НОВЫЙ МАРШРУТ: Информация о лиде для заявки
@bookings_bp.route('/<int:booking_id>/lead', methods=['GET'])
def get_booking_lead(booking_id):
    """Получить информацию о лиде, связанном с заявкой"""
    booking = Booking.query.get_or_404(booking_id)
    
    lead = None
    if hasattr(booking, 'source_lead') and booking.source_lead:
        lead = booking.source_lead
    elif hasattr(booking, 'lead_id') and booking.lead_id:
        lead = Lead.query.get(booking.lead_id)
    else:
        # Ищем лид по телефону
        lead = Lead.find_by_phone(booking.phone)
    
    if not lead:
        return jsonify({'error': 'Лид не найден'}), 404
    
    return jsonify({'lead': lead.to_dict(include_personal=True)})

# 🆕 НОВЫЙ МАРШРУТ: Создать лид из заявки вручную
@bookings_bp.route('/<int:booking_id>/create-lead', methods=['POST'])
def create_lead_from_booking(booking_id):
    """Создать лид из заявки вручную (если не был создан автоматически)"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем, нет ли уже лида для этого телефона
    existing_lead = Lead.find_by_phone(booking.phone)
    if existing_lead:
        # Связываем заявку с существующим лидом
        if hasattr(booking, 'lead_id'):
            booking.lead_id = existing_lead.id
            db.session.commit()
        
        return jsonify({
            'success': True,
            'lead': existing_lead.to_dict(include_personal=True),
            'message': f'Заявка связана с существующим лидом #{existing_lead.id}'
        })
    
    # Создаем нового лида
    booking_data = {
        'name': booking.name,
        'phone': booking.phone,
        'email': booking.email,
        'service_title': booking.service_title,
        'event_date': booking.event_date.strftime('%Y-%m-%d') if booking.event_date else None,
        'guests_count': booking.guests_count,
        'location': booking.location,
        'budget': booking.budget,
        'message': booking.message
    }
    
    lead = find_or_create_lead_from_booking(booking_data)
    
    if lead:
        # Связываем заявку с новым лидом
        if hasattr(booking, 'lead_id'):
            booking.lead_id = lead.id
        
        # Обновляем статус лида в зависимости от статуса заявки
        if booking.status == 'completed':
            lead.status = 'converted'
            lead.converted_at = booking.updated_at or datetime.utcnow()
        elif booking.status in ['confirmed', 'in-progress']:
            lead.status = 'qualified'
            lead.temperature = 'hot'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': f'Создан новый лид #{lead.id} из заявки'
        })
    else:
        return jsonify({'error': 'Не удалось создать лид'}), 500

# Дополнительный маршрут для отладки Telegram (остается без изменений)
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

# Тестовый маршрут для Telegram (остается без изменений)
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