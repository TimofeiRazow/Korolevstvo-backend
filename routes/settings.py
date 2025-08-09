# routes/settings.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Settings
import json

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET'])
def get_public_settings():
    """Получить публичные настройки (без авторизации)"""
    public_categories = ['company', 'social']
    settings = {}
    
    for category in public_categories:
        settings.update(Settings.get_settings_dict(category))
    
    return jsonify(settings)

@settings_bp.route('/admin/settings', methods=['GET'])
@jwt_required()
def get_all_settings():
    """Получить все настройки для админа"""
    category = request.args.get('category')
    
    if category:
        settings = Settings.get_settings_dict(category)
    else:
        settings = Settings.get_settings_dict()
    
    return jsonify(settings)

@settings_bp.route('/admin/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Обновить настройки"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных для обновления'}), 400
    
    try:
        updated_count = 0
        
        # Определение типов и категорий для каждого ключа
        setting_config = {
            # Компания
            'company_name': ('string', 'company'),
            'company_email': ('string', 'company'),
            'company_phone': ('string', 'company'),
            'whatsapp_phone': ('string', 'company'),
            'company_address': ('string', 'company'),
            'company_description': ('string', 'company'),
            
            # Социальные сети
            'social_instagram': ('string', 'social'),
            'social_facebook': ('string', 'social'),
            'social_youtube': ('string', 'social'),
            'social_telegram': ('string', 'social'),
            
            # Уведомления
            'email_notifications': ('boolean', 'notifications'),
            'telegram_notifications': ('boolean', 'notifications'),
            'sms_notifications': ('boolean', 'notifications'),
            'notification_email': ('string', 'notifications'),
            
            # SEO
            'site_title': ('string', 'seo'),
            'site_description': ('string', 'seo'),
            'site_keywords': ('string', 'seo'),
            'google_analytics_id': ('string', 'seo'),
            'yandex_metrica_id': ('string', 'seo'),
            
            # Интеграции
            'kaspi_api_key': ('string', 'integration'),
            'one_c_url': ('string', 'integration'),
            'smtp_server': ('string', 'integration'),
            'smtp_port': ('string', 'integration'),
        }
        
        for key, value in data.items():
            if key in setting_config:
                value_type, category = setting_config[key]
                Settings.update_setting(key, value, value_type, category)
                updated_count += 1
        
        return jsonify({
            'message': f'Обновлено {updated_count} настроек',
            'updated_count': updated_count
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при обновлении настроек: {str(e)}'}), 500

@settings_bp.route('/admin/settings/<string:key>', methods=['GET'])
@jwt_required()
def get_setting(key):
    """Получить одну настройку"""
    value = Settings.get_setting(key)
    
    if value is None:
        return jsonify({'error': 'Настройка не найдена'}), 404
    
    return jsonify({
        'key': key,
        'value': value
    })

@settings_bp.route('/admin/settings/<string:key>', methods=['PUT'])
@jwt_required()
def update_setting(key):
    """Обновить одну настройку"""
    data = request.get_json()
    value = data.get('value')
    value_type = data.get('value_type', 'string')
    category = data.get('category')
    
    try:
        Settings.update_setting(key, value, value_type, category)
        
        return jsonify({
            'message': f'Настройка {key} обновлена',
            'key': key,
            'value': value
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при обновлении настройки: {str(e)}'}), 500

@settings_bp.route('/admin/settings/categories', methods=['GET'])
@jwt_required()
def get_settings_by_categories():
    """Получить настройки, сгруппированные по категориям"""
    categories = ['company', 'social', 'notifications', 'seo', 'integration']
    result = {}
    
    for category in categories:
        result[category] = Settings.get_settings_dict(category)
    
    return jsonify(result)

@settings_bp.route('/admin/settings/init', methods=['POST'])
@jwt_required()
def init_default_settings():
    """Инициализировать настройки по умолчанию"""
    try:
        Settings.init_default_settings()
        return jsonify({'message': 'Настройки по умолчанию инициализированы'})
    except Exception as e:
        return jsonify({'error': f'Ошибка при инициализации: {str(e)}'}), 500