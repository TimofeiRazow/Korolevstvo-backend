<<<<<<< HEAD
# routes/leads.py
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func, or_, and_, desc
from datetime import datetime, timedelta
from models import db, Lead, Booking, Admin
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

leads_bp = Blueprint('leads', __name__)
logger = logging.getLogger(__name__)

# Константы для статусов и источников
LEAD_STATUSES = ['new', 'contacted', 'interested', 'qualified', 'converted', 'lost']
LEAD_STAGES = ['awareness', 'interest', 'consideration', 'intent', 'evaluation', 'purchase']
LEAD_TEMPERATURES = ['cold', 'warm', 'hot']
LEAD_SOURCES = ['website', 'instagram', 'whatsapp', 'referral', 'google', 'yandex', 'facebook', 'telegram', 'other']

@leads_bp.route('/', methods=['GET'])
@jwt_required()
def get_leads():
    """Получить список лидов с фильтрацией и пагинацией"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Фильтры
        status = request.args.get('status')
        source = request.args.get('source')
        temperature = request.args.get('temperature')
        assigned_to = request.args.get('assigned_to', type=int)
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        birthday_soon = request.args.get('birthday_soon', type=bool)
        
        # Сортировка
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Базовый запрос
        query = Lead.query
        
        # Применяем фильтры
        if status:
            query = query.filter(Lead.status == status)
        
        if source:
            query = query.filter(Lead.source == source)
            
        if temperature:
            query = query.filter(Lead.temperature == temperature)
            
        if assigned_to:
            query = query.filter(Lead.assigned_to == assigned_to)
        
        # Поиск по имени, телефону, email
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Lead.name.ilike(search_filter),
                    Lead.phone.ilike(search_filter),
                    Lead.email.ilike(search_filter),
                    Lead.notes.ilike(search_filter)
                )
            )
        
        # Фильтр по датам
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', ''))
                query = query.filter(Lead.created_at >= date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', ''))
                query = query.filter(Lead.created_at <= date_to_obj)
            except ValueError:
                pass
        
        # Фильтр по близким дням рождения
        if birthday_soon:
            today = datetime.utcnow().date()
            next_month = today + timedelta(days=30)
            leads_with_birthdays = Lead.get_birthday_leads(30)
            lead_ids = [lead.id for lead in leads_with_birthdays]
            if lead_ids:
                query = query.filter(Lead.id.in_(lead_ids))
            else:
                query = query.filter(Lead.id == -1)  # Пустой результат
        
        # Сортировка
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(Lead, sort_by, Lead.created_at)))
        else:
            query = query.order_by(getattr(Lead, sort_by, Lead.created_at))
        
        # Пагинация
        leads_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Преобразуем в список словарей
        leads_list = [lead.to_dict(include_personal=True) for lead in leads_pagination.items]
        
        return jsonify({
            'success': True,
            'leads': leads_list,
            'pagination': {
                'page': page,
                'pages': leads_pagination.pages,
                'per_page': per_page,
                'total': leads_pagination.total,
                'has_next': leads_pagination.has_next,
                'has_prev': leads_pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return jsonify({'error': 'Ошибка при загрузке лидов'}), 500


@leads_bp.route('/<int:lead_id>', methods=['GET'])
@jwt_required()
def get_lead(lead_id):
    """Получить информацию о конкретном лиде"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        # Получаем связанные заявки
        bookings = lead.bookings.all()
        
        lead_data = lead.to_dict(include_personal=True)
        lead_data['bookings'] = [booking.to_dict() for booking in bookings]
        
        return jsonify({
            'success': True,
            'lead': lead_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        return jsonify({'error': 'Лид не найден'}), 404


@leads_bp.route('/', methods=['POST'])
@jwt_required()
def create_lead():
    """Создать нового лида"""
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Имя и телефон обязательны'}), 400
        
        # Проверяем, не существует ли уже лид с таким телефоном
        existing_lead = Lead.find_by_phone(data['phone'])
        if existing_lead:
            return jsonify({
                'error': 'Лид с таким номером телефона уже существует',
                'existing_lead_id': existing_lead.id
            }), 400
        
        # Создаем нового лида
        lead = Lead()
        lead.update_from_dict(data)
        
        # Автоматически назначаем текущему пользователю, если не указано
        if not lead.assigned_to:
            lead.assigned_to = g.current_user.id
        
        # Рассчитываем качество лида
        lead.calculate_quality_score()
        
        db.session.add(lead)
        db.session.commit()
        
        logger.info(f"Created new lead {lead.id} by user {g.current_user.id}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': 'Лид успешно создан'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating lead: {e}")
        return jsonify({'error': 'Ошибка при создании лида'}), 500


@leads_bp.route('/<int:lead_id>', methods=['PUT'])
@jwt_required()
def update_lead(lead_id):
    """Обновить информацию о лиде"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json()
        
        # Обновляем данные
        lead.update_from_dict(data)
        
        # Пересчитываем качество лида
        lead.calculate_quality_score()
        
        db.session.commit()
        
        logger.info(f"Updated lead {lead_id} by user {g.current_user.id}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': 'Лид успешно обновлен'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при обновлении лида'}), 500


@leads_bp.route('/<int:lead_id>', methods=['DELETE'])
@jwt_required()
def delete_lead(lead_id):
    """Удалить лида"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        # Проверяем, есть ли связанные заявки
        if lead.bookings.count() > 0:
            return jsonify({
                'error': 'Нельзя удалить лида с привязанными заявками'
            }), 400
        
        db.session.delete(lead)
        db.session.commit()
        
        logger.info(f"Deleted lead {lead_id} by user {g.current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Лид успешно удален'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при удалении лида'}), 500


@leads_bp.route('/<int:lead_id>/contact', methods=['POST'])
@jwt_required()
def add_contact_record(lead_id):
    """Добавить запись о контакте с лидом"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json()
        
        contact_date = data.get('contact_date')
        result = data.get('result')  # answered, no_answer, not_interested, interested
        notes = data.get('notes', '')
        
        # Обновляем информацию о контакте
        if contact_date:
            try:
                contact_date_obj = datetime.fromisoformat(contact_date.replace('Z', ''))
            except:
                contact_date_obj = datetime.utcnow()
        else:
            contact_date_obj = datetime.utcnow()
        
        lead.update_contact_info(contact_date_obj, result)
        
        # Добавляем заметки
        if notes:
            current_notes = lead.notes or ''
            timestamp = contact_date_obj.strftime('%Y-%m-%d %H:%M')
            new_note = f"\n[{timestamp}] Контакт: {notes}"
            lead.notes = current_notes + new_note
        
        db.session.commit()
        
        logger.info(f"Added contact record for lead {lead_id} by user {g.current_user.id}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': 'Запись о контакте добавлена'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding contact record for lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при добавлении записи о контакте'}), 500


@leads_bp.route('/<int:lead_id>/convert', methods=['POST'])
@jwt_required()
def convert_lead_to_booking(lead_id):
    """Конвертировать лида в заявку"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json() or {}
        
        # Проверяем, не конвертирован ли уже лид
        if lead.status == 'converted':
            return jsonify({
                'error': 'Лид уже конвертирован в заявку'
            }), 400
        
        # Создаем заявку
        booking = lead.convert_to_booking(data)
        
        if not booking:
            return jsonify({'error': 'Не удалось конвертировать лид'}), 400
        
        db.session.commit()
        
        logger.info(f"Converted lead {lead_id} to booking {booking.id} by user {g.current_user.id}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'booking': booking.to_dict(),
            'message': 'Лид успешно конвертирован в заявку'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error converting lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при конверсии лида'}), 500


@leads_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_leads_stats():
    """Получить статистику лидов"""
    try:
        period_days = request.args.get('period', 30, type=int)
        
        # Основная статистика
        stats = Lead.get_stats(period_days)
        
        # Дополнительная статистика
        today = datetime.utcnow().date()
        
        # Лиды с днями рождения в ближайшие 30 дней
        birthday_leads = Lead.get_birthday_leads(30)
        
        # Лиды, требующие контакта
        overdue_leads = Lead.query.filter(
            Lead.next_follow_up < datetime.utcnow(),
            Lead.status.in_(['new', 'contacted', 'interested'])
        ).count()
        from sqlalchemy import func, case
        # Статистика по менеджерам
        manager_stats = db.session.query(
            Admin.name,
            func.count(Lead.id).label('leads_count'),
            func.sum(case((Lead.status == 'converted', 1), else_=0)).label('converted_count')
        ).join(Lead, Admin.id == Lead.assigned_to)\
        .filter(Lead.created_at >= datetime.utcnow() - timedelta(days=period_days))\
        .group_by(Admin.id, Admin.name).all()
        
        # Среднее время до конверсии
        converted_leads = Lead.query.filter(
            Lead.status == 'converted',
            Lead.converted_at.isnot(None),
            Lead.created_at >= datetime.utcnow() - timedelta(days=period_days)
        ).all()
        
        if converted_leads:
            total_time = sum([
                (lead.converted_at - lead.created_at).total_seconds()
                for lead in converted_leads
            ])
            avg_conversion_time_hours = (total_time / len(converted_leads)) / 3600
        else:
            avg_conversion_time_hours = 0
        
        stats.update({
            'birthday_leads_count': len(birthday_leads),
            'birthday_leads': [lead.to_dict(include_personal=True) for lead in birthday_leads[:10]],
            'overdue_leads_count': overdue_leads,
            'avg_conversion_time_hours': round(avg_conversion_time_hours, 1),
            'managers': [
                {
                    'name': name,
                    'leads_count': leads_count,
                    'converted_count': converted_count,
                    'conversion_rate': round((converted_count / leads_count * 100), 1) if leads_count > 0 else 0
                }
                for name, leads_count, converted_count in manager_stats
            ]
        })
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting leads stats: {e}")
        return jsonify({'error': 'Ошибка при получении статистики'}), 500


@leads_bp.route('/birthday', methods=['GET'])
@jwt_required()
def get_birthday_leads():
    """Получить лидов с приближающимися днями рождения"""
    try:
        days_ahead = request.args.get('days', 30, type=int)
        
        birthday_leads = Lead.get_birthday_leads(days_ahead)
        
        leads_data = []
        for lead in birthday_leads:
            lead_data = lead.to_dict(include_personal=True)
            
            # Добавляем информацию о дне рождения
            if lead.birthday:
                today = datetime.utcnow().date()
                this_year_birthday = lead.birthday.replace(year=today.year)
                if this_year_birthday < today:
                    next_birthday = lead.birthday.replace(year=today.year + 1)
                else:
                    next_birthday = this_year_birthday
                
                lead_data.update({
                    'days_until_birthday': (next_birthday - today).days,
                    'next_birthday': next_birthday.isoformat(),
                    'age_turning': today.year - lead.birthday.year if next_birthday.year == today.year else today.year - lead.birthday.year + 1
                })
            
            leads_data.append(lead_data)
        
        # Сортируем по близости дня рождения
        leads_data.sort(key=lambda x: x.get('days_until_birthday', 999))
        
        return jsonify({
            'success': True,
            'leads': leads_data,
            'total': len(leads_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting birthday leads: {e}")
        return jsonify({'error': 'Ошибка при получении лидов с днями рождения'}), 500


@leads_bp.route('/import', methods=['POST'])
@jwt_required()
def import_leads():
    """Импорт лидов из CSV или создание из заявок"""
    try:
        data = request.get_json()
        import_type = data.get('type', 'csv')  # csv, bookings
        
        if import_type == 'bookings':
            # Создаем лидов из существующих заявок, которые еще не связаны с лидами
            bookings_without_leads = Booking.query.filter(
                Booking.lead_id.is_(None)
            ).all()
            
            created_leads = []
            for booking in bookings_without_leads:
                lead = Lead.create_from_booking(booking)
                if lead:
                    db.session.add(lead)
                    created_leads.append(lead)
            
            db.session.commit()
            
            logger.info(f"Imported {len(created_leads)} leads from bookings by user {g.current_user.id}")
            
            return jsonify({
                'success': True,
                'imported_count': len(created_leads),
                'leads': [lead.to_dict() for lead in created_leads[:10]],
                'message': f'Импортировано {len(created_leads)} лидов из заявок'
            })
        
        else:
            # TODO: Реализовать импорт из CSV
            return jsonify({'error': 'CSV импорт пока не реализован'}), 501
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing leads: {e}")
        return jsonify({'error': 'Ошибка при импорте лидов'}), 500


@leads_bp.route('/export', methods=['GET'])
@jwt_required()
def export_leads():
    """Экспорт лидов в CSV"""
    try:
        # Параметры фильтрации (аналогично get_leads)
        status = request.args.get('status')
        source = request.args.get('source')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = Lead.query
        
        # Применяем фильтры
        if status:
            query = query.filter(Lead.status == status)
        if source:
            query = query.filter(Lead.source == source)
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', ''))
                query = query.filter(Lead.created_at >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', ''))
                query = query.filter(Lead.created_at <= date_to_obj)
            except ValueError:
                pass
        
        leads = query.all()
        
        # Подготавливаем данные для экспорта
        export_data = []
        for lead in leads:
            lead_dict = lead.to_dict(include_personal=True)
            export_data.append({
                'ID': lead_dict['id'],
                'Имя': lead_dict['name'],
                'Телефон': lead_dict['phone'],
                'Email': lead_dict.get('email', ''),
                'Источник': lead_dict['source'],
                'Статус': lead_dict['status'],
                'Температура': lead_dict['temperature'],
                'Бюджет': lead_dict.get('preferred_budget', ''),
                'Тип события': lead_dict.get('event_type', ''),
                'Количество гостей': lead_dict.get('guests_count', ''),
                'День рождения': lead_dict.get('birthday', ''),
                'Возраст': lead_dict.get('age', ''),
                'Заметки': lead_dict.get('notes', ''),
                'Менеджер': lead_dict.get('assigned_manager_name', ''),
                'Дата создания': lead_dict['created_at'],
                'Качество лида': lead_dict['quality_score']
            })
        
        return jsonify({
            'success': True,
            'data': export_data,
            'count': len(export_data),
            'message': f'Экспортировано {len(export_data)} лидов'
        })
        
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        return jsonify({'error': 'Ошибка при экспорте лидов'}), 500


@leads_bp.route('/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_leads():
    """Массовое обновление лидов"""
    try:
        data = request.get_json()
        lead_ids = data.get('lead_ids', [])
        updates = data.get('updates', {})
        
        if not lead_ids or not updates:
            return jsonify({'error': 'Не указаны лиды для обновления или данные для обновления'}), 400
        
        # Получаем лидов
        leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
        
        if not leads:
            return jsonify({'error': 'Лиды не найдены'}), 404
        
        updated_count = 0
        for lead in leads:
            # Обновляем только разрешенные поля
            allowed_updates = {
                'status', 'temperature', 'assigned_to', 'source', 
                'next_follow_up', 'tags', 'notes'
            }
            
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
            
            if filtered_updates:
                lead.update_from_dict(filtered_updates)
                updated_count += 1
        
        db.session.commit()
        
        logger.info(f"Bulk updated {updated_count} leads by user {g.current_user.id}")
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'message': f'Обновлено {updated_count} лидов'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error bulk updating leads: {e}")
        return jsonify({'error': 'Ошибка при массовом обновлении лидов'}), 500


@leads_bp.route('/constants', methods=['GET'])
def get_lead_constants():
    """Получить константы для работы с лидами"""
    return jsonify({
        'success': True,
        'constants': {
            'statuses': LEAD_STATUSES,
            'stages': LEAD_STAGES,
            'temperatures': LEAD_TEMPERATURES,
            'sources': LEAD_SOURCES,
            'status_labels': {
                'new': 'Новый',
                'contacted': 'Связались',
                'interested': 'Заинтересован',
                'qualified': 'Квалифицирован',
                'converted': 'Конвертирован',
                'lost': 'Потерян'
            },
            'temperature_labels': {
                'cold': 'Холодный',
                'warm': 'Теплый',
                'hot': 'Горячий'
            },
            'source_labels': {
                'website': 'Сайт',
                'instagram': 'Instagram',
                'whatsapp': 'WhatsApp',
                'referral': 'Рекомендация',
                'google': 'Google',
                'yandex': 'Яндекс',
                'facebook': 'Facebook',
                'telegram': 'Telegram',
                'other': 'Другое'
            }
        }
    })


@leads_bp.route('/funnel', methods=['GET'])
@jwt_required()
def get_leads_funnel():
    """Получить данные воронки лидов"""
    try:
        period_days = request.args.get('period', 30, type=int)
        date_from = datetime.utcnow() - timedelta(days=period_days)
        
        # Подсчитываем лидов на каждом этапе воронки
        funnel_data = []
        
        # Этапы воронки в порядке
        funnel_stages = [
            ('new', 'Новые лиды'),
            ('contacted', 'Первый контакт'),
            ('interested', 'Проявили интерес'),
            ('qualified', 'Квалифицированы'),
            ('converted', 'Конвертированы')
        ]
        
        total_leads = Lead.query.filter(Lead.created_at >= date_from).count()
        
        for status, label in funnel_stages:
            count = Lead.query.filter(
                Lead.created_at >= date_from,
                Lead.status == status
            ).count()
            
            percentage = (count / total_leads * 100) if total_leads > 0 else 0
            
            funnel_data.append({
                'stage': status,
                'label': label,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return jsonify({
            'success': True,
            'funnel': funnel_data,
            'total_leads': total_leads,
            'period_days': period_days
        })
        
    except Exception as e:
        logger.error(f"Error getting leads funnel: {e}")
=======
# routes/leads.py
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func, or_, and_, desc
from datetime import datetime, timedelta
from models import db, Lead, Booking, Admin
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

leads_bp = Blueprint('leads', __name__)
logger = logging.getLogger(__name__)

# Константы для статусов и источников
LEAD_STATUSES = ['new', 'contacted', 'interested', 'qualified', 'converted', 'lost']
LEAD_STAGES = ['awareness', 'interest', 'consideration', 'intent', 'evaluation', 'purchase']
LEAD_TEMPERATURES = ['cold', 'warm', 'hot']
LEAD_SOURCES = ['website', 'instagram', 'whatsapp', 'referral', 'google', 'yandex', 'facebook', 'telegram', 'other']

@leads_bp.route('/', methods=['GET'])
@jwt_required()
def get_leads():
    """Получить список лидов с фильтрацией и пагинацией"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Фильтры
        status = request.args.get('status')
        source = request.args.get('source')
        temperature = request.args.get('temperature')
        assigned_to = request.args.get('assigned_to', type=int)
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        birthday_soon = request.args.get('birthday_soon', type=bool)
        
        # Сортировка
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Базовый запрос
        query = Lead.query
        
        # Применяем фильтры
        if status:
            query = query.filter(Lead.status == status)
        
        if source:
            query = query.filter(Lead.source == source)
            
        if temperature:
            query = query.filter(Lead.temperature == temperature)
            
        if assigned_to:
            query = query.filter(Lead.assigned_to == assigned_to)
        
        # Поиск по имени, телефону, email
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Lead.name.ilike(search_filter),
                    Lead.phone.ilike(search_filter),
                    Lead.email.ilike(search_filter),
                    Lead.notes.ilike(search_filter)
                )
            )
        
        # Фильтр по датам
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', ''))
                query = query.filter(Lead.created_at >= date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', ''))
                query = query.filter(Lead.created_at <= date_to_obj)
            except ValueError:
                pass
        
        # Фильтр по близким дням рождения
        if birthday_soon:
            today = datetime.utcnow().date()
            next_month = today + timedelta(days=30)
            leads_with_birthdays = Lead.get_birthday_leads(30)
            lead_ids = [lead.id for lead in leads_with_birthdays]
            if lead_ids:
                query = query.filter(Lead.id.in_(lead_ids))
            else:
                query = query.filter(Lead.id == -1)  # Пустой результат
        
        # Сортировка
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(Lead, sort_by, Lead.created_at)))
        else:
            query = query.order_by(getattr(Lead, sort_by, Lead.created_at))
        
        # Пагинация
        leads_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Преобразуем в список словарей
        leads_list = [lead.to_dict(include_personal=True) for lead in leads_pagination.items]
        
        return jsonify({
            'success': True,
            'leads': leads_list,
            'pagination': {
                'page': page,
                'pages': leads_pagination.pages,
                'per_page': per_page,
                'total': leads_pagination.total,
                'has_next': leads_pagination.has_next,
                'has_prev': leads_pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return jsonify({'error': 'Ошибка при загрузке лидов'}), 500


@leads_bp.route('/<int:lead_id>', methods=['GET'])
@jwt_required()
def get_lead(lead_id):
    """Получить информацию о конкретном лиде"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        # Получаем связанные заявки
        bookings = lead.bookings.all()
        
        lead_data = lead.to_dict(include_personal=True)
        lead_data['bookings'] = [booking.to_dict() for booking in bookings]
        
        return jsonify({
            'success': True,
            'lead': lead_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        return jsonify({'error': 'Лид не найден'}), 404


@leads_bp.route('/', methods=['POST'])
@jwt_required()
def create_lead():
    """Создать нового лида"""
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Имя и телефон обязательны'}), 400
        
        # Проверяем, не существует ли уже лид с таким телефоном
        existing_lead = Lead.find_by_phone(data['phone'])
        if existing_lead:
            return jsonify({
                'error': 'Лид с таким номером телефона уже существует',
                'existing_lead_id': existing_lead.id
            }), 400
        
        # Создаем нового лида
        lead = Lead()
        lead.update_from_dict(data)
        
        # Автоматически назначаем текущему пользователю, если не указано
        if not lead.assigned_to:
            
            lead.assigned_to = int(get_jwt_identity())
        
        # Рассчитываем качество лида
        lead.calculate_quality_score()
        
        db.session.add(lead)
        db.session.commit()
        
        logger.info(f"Created new lead {lead.id} by user {int(get_jwt_identity())}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': 'Лид успешно создан'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating lead: {e}")
        return jsonify({'error': 'Ошибка при создании лида'}), 500


@leads_bp.route('/<int:lead_id>', methods=['PUT'])
@jwt_required()
def update_lead(lead_id):
    """Обновить информацию о лиде"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json()
        
        # Обновляем данные
        lead.update_from_dict(data)
        
        # Пересчитываем качество лида
        lead.calculate_quality_score()
        
        db.session.commit()
        
        logger.info(f"Updated lead {lead_id} by user {int(get_jwt_identity())}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': 'Лид успешно обновлен'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при обновлении лида'}), 500


@leads_bp.route('/<int:lead_id>', methods=['DELETE'])
@jwt_required()
def delete_lead(lead_id):
    """Удалить лида"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        # Проверяем, есть ли связанные заявки
        if lead.bookings.count() > 0:
            return jsonify({
                'error': 'Нельзя удалить лида с привязанными заявками'
            }), 400
        
        db.session.delete(lead)
        db.session.commit()
        
        logger.info(f"Deleted lead {lead_id} by user {int(get_jwt_identity())}")
        
        return jsonify({
            'success': True,
            'message': 'Лид успешно удален'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при удалении лида'}), 500


@leads_bp.route('/<int:lead_id>/contact', methods=['POST'])
@jwt_required()
def add_contact_record(lead_id):
    """Добавить запись о контакте с лидом"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json()
        
        contact_date = data.get('contact_date')
        result = data.get('result')  # answered, no_answer, not_interested, interested
        notes = data.get('notes', '')
        
        # Обновляем информацию о контакте
        if contact_date:
            try:
                contact_date_obj = datetime.fromisoformat(contact_date.replace('Z', ''))
            except:
                contact_date_obj = datetime.utcnow()
        else:
            contact_date_obj = datetime.utcnow()
        
        lead.update_contact_info(contact_date_obj, result)
        
        # Добавляем заметки
        if notes:
            current_notes = lead.notes or ''
            timestamp = contact_date_obj.strftime('%Y-%m-%d %H:%M')
            new_note = f"\n[{timestamp}] Контакт: {notes}"
            lead.notes = current_notes + new_note
        
        db.session.commit()
        
        logger.info(f"Added contact record for lead {lead_id} by user {int(get_jwt_identity())}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'message': 'Запись о контакте добавлена'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding contact record for lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при добавлении записи о контакте'}), 500


@leads_bp.route('/<int:lead_id>/convert', methods=['POST'])
@jwt_required()
def convert_lead_to_booking(lead_id):
    """Конвертировать лида в заявку"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json() or {}
        
        # Проверяем, не конвертирован ли уже лид
        if lead.status == 'converted':
            return jsonify({
                'error': 'Лид уже конвертирован в заявку'
            }), 400
        
        # Создаем заявку
        booking = lead.convert_to_booking(data)
        
        if not booking:
            return jsonify({'error': 'Не удалось конвертировать лид'}), 400
        
        db.session.commit()
        
        logger.info(f"Converted lead {lead_id} to booking {booking.id} by user {int(get_jwt_identity())}")
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict(include_personal=True),
            'booking': booking.to_dict(),
            'message': 'Лид успешно конвертирован в заявку'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error converting lead {lead_id}: {e}")
        return jsonify({'error': 'Ошибка при конверсии лида'}), 500


@leads_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_leads_stats():
    """Получить статистику лидов"""
    try:
        period_days = request.args.get('period', 30, type=int)
        
        # Основная статистика
        stats = Lead.get_stats(period_days)
        
        # Дополнительная статистика
        today = datetime.utcnow().date()
        
        # Лиды с днями рождения в ближайшие 30 дней
        birthday_leads = Lead.get_birthday_leads(30)
        
        # Лиды, требующие контакта
        overdue_leads = Lead.query.filter(
            Lead.next_follow_up < datetime.utcnow(),
            Lead.status.in_(['new', 'contacted', 'interested'])
        ).count()
        from sqlalchemy import func, case
        # Статистика по менеджерам
        manager_stats = db.session.query(
            Admin.name,
            func.count(Lead.id).label('leads_count'),
            func.sum(case((Lead.status == 'converted', 1), else_=0)).label('converted_count')
        ).join(Lead, Admin.id == Lead.assigned_to)\
        .filter(Lead.created_at >= datetime.utcnow() - timedelta(days=period_days))\
        .group_by(Admin.id, Admin.name).all()
        
        # Среднее время до конверсии
        converted_leads = Lead.query.filter(
            Lead.status == 'converted',
            Lead.converted_at.isnot(None),
            Lead.created_at >= datetime.utcnow() - timedelta(days=period_days)
        ).all()
        
        if converted_leads:
            total_time = sum([
                (lead.converted_at - lead.created_at).total_seconds()
                for lead in converted_leads
            ])
            avg_conversion_time_hours = (total_time / len(converted_leads)) / 3600
        else:
            avg_conversion_time_hours = 0
        
        stats.update({
            'birthday_leads_count': len(birthday_leads),
            'birthday_leads': [lead.to_dict(include_personal=True) for lead in birthday_leads[:10]],
            'overdue_leads_count': overdue_leads,
            'avg_conversion_time_hours': round(avg_conversion_time_hours, 1),
            'managers': [
                {
                    'name': name,
                    'leads_count': leads_count,
                    'converted_count': converted_count,
                    'conversion_rate': round((converted_count / leads_count * 100), 1) if leads_count > 0 else 0
                }
                for name, leads_count, converted_count in manager_stats
            ]
        })
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting leads stats: {e}")
        return jsonify({'error': 'Ошибка при получении статистики'}), 500


@leads_bp.route('/birthday', methods=['GET'])
@jwt_required()
def get_birthday_leads():
    """Получить лидов с приближающимися днями рождения"""
    try:
        days_ahead = request.args.get('days', 30, type=int)
        
        birthday_leads = Lead.get_birthday_leads(days_ahead)
        
        leads_data = []
        for lead in birthday_leads:
            lead_data = lead.to_dict(include_personal=True)
            
            # Добавляем информацию о дне рождения
            if lead.birthday:
                today = datetime.utcnow().date()
                this_year_birthday = lead.birthday.replace(year=today.year)
                if this_year_birthday < today:
                    next_birthday = lead.birthday.replace(year=today.year + 1)
                else:
                    next_birthday = this_year_birthday
                
                lead_data.update({
                    'days_until_birthday': (next_birthday - today).days,
                    'next_birthday': next_birthday.isoformat(),
                    'age_turning': today.year - lead.birthday.year if next_birthday.year == today.year else today.year - lead.birthday.year + 1
                })
            
            leads_data.append(lead_data)
        
        # Сортируем по близости дня рождения
        leads_data.sort(key=lambda x: x.get('days_until_birthday', 999))
        
        return jsonify({
            'success': True,
            'leads': leads_data,
            'total': len(leads_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting birthday leads: {e}")
        return jsonify({'error': 'Ошибка при получении лидов с днями рождения'}), 500


@leads_bp.route('/import', methods=['POST'])
@jwt_required()
def import_leads():
    """Импорт лидов из CSV или создание из заявок"""
    try:
        data = request.get_json()
        import_type = data.get('type', 'csv')  # csv, bookings
        
        if import_type == 'bookings':
            # Создаем лидов из существующих заявок, которые еще не связаны с лидами
            bookings_without_leads = Booking.query.filter(
                Booking.lead_id.is_(None)
            ).all()
            
            created_leads = []
            for booking in bookings_without_leads:
                lead = Lead.create_from_booking(booking)
                if lead:
                    db.session.add(lead)
                    created_leads.append(lead)
            
            db.session.commit()
            
            logger.info(f"Imported {len(created_leads)} leads from bookings by user {int(get_jwt_identity())}")
            
            return jsonify({
                'success': True,
                'imported_count': len(created_leads),
                'leads': [lead.to_dict() for lead in created_leads[:10]],
                'message': f'Импортировано {len(created_leads)} лидов из заявок'
            })
        
        else:
            # TODO: Реализовать импорт из CSV
            return jsonify({'error': 'CSV импорт пока не реализован'}), 501
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing leads: {e}")
        return jsonify({'error': 'Ошибка при импорте лидов'}), 500


@leads_bp.route('/export', methods=['GET'])
@jwt_required()
def export_leads():
    """Экспорт лидов в CSV"""
    try:
        # Параметры фильтрации (аналогично get_leads)
        status = request.args.get('status')
        source = request.args.get('source')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = Lead.query
        
        # Применяем фильтры
        if status:
            query = query.filter(Lead.status == status)
        if source:
            query = query.filter(Lead.source == source)
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', ''))
                query = query.filter(Lead.created_at >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', ''))
                query = query.filter(Lead.created_at <= date_to_obj)
            except ValueError:
                pass
        
        leads = query.all()
        
        # Подготавливаем данные для экспорта
        export_data = []
        for lead in leads:
            lead_dict = lead.to_dict(include_personal=True)
            export_data.append({
                'ID': lead_dict['id'],
                'Имя': lead_dict['name'],
                'Телефон': lead_dict['phone'],
                'Email': lead_dict.get('email', ''),
                'Источник': lead_dict['source'],
                'Статус': lead_dict['status'],
                'Температура': lead_dict['temperature'],
                'Бюджет': lead_dict.get('preferred_budget', ''),
                'Тип события': lead_dict.get('event_type', ''),
                'Количество гостей': lead_dict.get('guests_count', ''),
                'День рождения': lead_dict.get('birthday', ''),
                'Возраст': lead_dict.get('age', ''),
                'Заметки': lead_dict.get('notes', ''),
                'Менеджер': lead_dict.get('assigned_manager_name', ''),
                'Дата создания': lead_dict['created_at'],
                'Качество лида': lead_dict['quality_score']
            })
        
        return jsonify({
            'success': True,
            'data': export_data,
            'count': len(export_data),
            'message': f'Экспортировано {len(export_data)} лидов'
        })
        
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        return jsonify({'error': 'Ошибка при экспорте лидов'}), 500


@leads_bp.route('/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_leads():
    """Массовое обновление лидов"""
    try:
        data = request.get_json()
        lead_ids = data.get('lead_ids', [])
        updates = data.get('updates', {})
        
        if not lead_ids or not updates:
            return jsonify({'error': 'Не указаны лиды для обновления или данные для обновления'}), 400
        
        # Получаем лидов
        leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
        
        if not leads:
            return jsonify({'error': 'Лиды не найдены'}), 404
        
        updated_count = 0
        for lead in leads:
            # Обновляем только разрешенные поля
            allowed_updates = {
                'status', 'temperature', 'assigned_to', 'source', 
                'next_follow_up', 'tags', 'notes'
            }
            
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
            
            if filtered_updates:
                lead.update_from_dict(filtered_updates)
                updated_count += 1
        
        db.session.commit()
        
        logger.info(f"Bulk updated {updated_count} leads by user {int(get_jwt_identity())}")
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'message': f'Обновлено {updated_count} лидов'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error bulk updating leads: {e}")
        return jsonify({'error': 'Ошибка при массовом обновлении лидов'}), 500


@leads_bp.route('/constants', methods=['GET'])
def get_lead_constants():
    """Получить константы для работы с лидами"""
    return jsonify({
        'success': True,
        'constants': {
            'statuses': LEAD_STATUSES,
            'stages': LEAD_STAGES,
            'temperatures': LEAD_TEMPERATURES,
            'sources': LEAD_SOURCES,
            'status_labels': {
                'new': 'Новый',
                'contacted': 'Связались',
                'interested': 'Заинтересован',
                'qualified': 'Квалифицирован',
                'converted': 'Конвертирован',
                'lost': 'Потерян'
            },
            'temperature_labels': {
                'cold': 'Холодный',
                'warm': 'Теплый',
                'hot': 'Горячий'
            },
            'source_labels': {
                'website': 'Сайт',
                'instagram': 'Instagram',
                'whatsapp': 'WhatsApp',
                'referral': 'Рекомендация',
                'google': 'Google',
                'yandex': 'Яндекс',
                'facebook': 'Facebook',
                'telegram': 'Telegram',
                'other': 'Другое'
            }
        }
    })


@leads_bp.route('/funnel', methods=['GET'])
@jwt_required()
def get_leads_funnel():
    """Получить данные воронки лидов"""
    try:
        period_days = request.args.get('period', 30, type=int)
        date_from = datetime.utcnow() - timedelta(days=period_days)
        
        # Подсчитываем лидов на каждом этапе воронки
        funnel_data = []
        
        # Этапы воронки в порядке
        funnel_stages = [
            ('new', 'Новые лиды'),
            ('contacted', 'Первый контакт'),
            ('interested', 'Проявили интерес'),
            ('qualified', 'Квалифицированы'),
            ('converted', 'Конвертированы')
        ]
        
        total_leads = Lead.query.filter(Lead.created_at >= date_from).count()
        
        for status, label in funnel_stages:
            count = Lead.query.filter(
                Lead.created_at >= date_from,
                Lead.status == status
            ).count()
            
            percentage = (count / total_leads * 100) if total_leads > 0 else 0
            
            funnel_data.append({
                'stage': status,
                'label': label,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return jsonify({
            'success': True,
            'funnel': funnel_data,
            'total_leads': total_leads,
            'period_days': period_days
        })
        
    except Exception as e:
        logger.error(f"Error getting leads funnel: {e}")
>>>>>>> 3f30d7d36d123e7da8c211f2a8b5f2aecd357aef
        return jsonify({'error': 'Ошибка при получении воронки лидов'}), 500