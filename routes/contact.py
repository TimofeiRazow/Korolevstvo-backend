# routes/contact.py
from flask import Blueprint, request, jsonify, current_app
from models import db, TeamMember
from utils.email import send_contact_message

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/info', methods=['GET'])
def get_contact_info():
    """Получить контактную информацию"""
    return jsonify({
        'contact_info': current_app.config['COMPANY_INFO'],
        'locations': [
            {
                'id': 1,
                'name': 'Главный офис',
                'address': 'ул. Конституции, 15, офис 201',
                'phone': '+7 (7152) 123-456',
                'hours': '9:00 - 21:00',
                'services': ['Консультации', 'Заключение договоров', 'Просмотр реквизита'],
                'coordinates': {'lat': 54.8684, 'lng': 69.1398}
            },
            {
                'id': 2,
                'name': 'Склад реквизита',
                'address': 'ул. Промышленная, 42',
                'phone': '+7 (7152) 123-457',
                'hours': '10:00 - 18:00',
                'services': ['Хранение костюмов', 'Подготовка реквизита', 'Выдача оборудования'],
                'coordinates': {'lat': 54.8584, 'lng': 69.1298}
            }
        ]
    })

@contact_bp.route('/feedback', methods=['POST'])
def send_feedback():
    """Отправить сообщение обратной связи"""
    data = request.get_json()
    
    required_fields = ['name', 'email', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Поле {field} обязательно'}), 400
    
    try:
        # Отправка email
        send_contact_message(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            subject=data.get('subject', 'Сообщение с сайта'),
            message=data['message']
        )
        
        return jsonify({
            'message': 'Сообщение отправлено! Мы ответим в ближайшее время.'
        }), 201
    
    except Exception as e:
        return jsonify({'error': 'Ошибка при отправке сообщения'}), 500

@contact_bp.route('/callback', methods=['POST'])
def request_callback():
    """Заказать обратный звонок"""
    data = request.get_json()
    
    if not data.get('phone'):
        return jsonify({'error': 'Номер телефона обязателен'}), 400
    
    try:
        # Отправка уведомления администратору
        send_contact_message(
            name=data.get('name', 'Заказ обратного звонка'),
            email='callback@prazdnikvdom.kz',
            phone=data['phone'],
            subject='Заказ обратного звонка',
            message=f"Удобное время для звонка: {data.get('preferred_time', 'любое время')}"
        )
        
        return jsonify({
            'message': 'Заявка принята! Мы перезвоним в течение 15 минут.'
        }), 201
    
    except Exception as e:
        return jsonify({'error': 'Ошибка при отправке заявки'}), 500