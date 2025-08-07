from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, Admin
from utils.validators import validate_admin_data
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def admin_login():
    """Вход администратора"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email и пароль обязательны'}), 400
    
    admin = Admin.query.filter_by(email=data['email'], active=True).first()
    
    if not admin or not admin.check_password(data['password']):
        return jsonify({'error': 'Неверные учетные данные'}), 401
    
    # Обновляем время последнего входа
    admin.update_last_login()
    
    # Создаем токен
    access_token = create_access_token(
        identity=admin.id,
        expires_delta=timedelta(hours=8),
        additional_claims={
            'role': admin.role,
            'email': admin.email,
            'name': admin.name
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'admin': admin.to_dict(),
        'message': 'Вход выполнен успешно'
    })

@auth_bp.route('/register', methods=['POST'])
@jwt_required()
def admin_register():
    """Регистрация нового администратора (только для существующих админов)"""
    current_admin_id = get_jwt_identity()
    current_admin = Admin.query.get(current_admin_id)
    
    if not current_admin or current_admin.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    data = request.get_json()
    
    # Валидация данных
    errors = validate_admin_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    # Проверяем, не существует ли уже админ с таким email
    existing_admin = Admin.query.filter_by(email=data['email']).first()
    if existing_admin:
        return jsonify({'error': 'Администратор с таким email уже существует'}), 400
    
    try:
        # Создаем нового администратора
        new_admin = Admin(
            name=data['name'],
            email=data['email'],
            role=data.get('role', 'admin'),
            created_by=current_admin_id
        )
        new_admin.set_password(data['password'])
        
        db.session.add(new_admin)
        db.session.commit()
        
        return jsonify({
            'admin': new_admin.to_dict(),
            'message': 'Администратор успешно создан'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при создании администратора'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_admin():
    """Получить данные текущего администратора"""
    admin_id = get_jwt_identity()
    admin = Admin.query.get(admin_id)
    
    if not admin or not admin.active:
        return jsonify({'error': 'Администратор не найден'}), 404
    
    return jsonify({'admin': admin.to_dict()})

@auth_bp.route('/admins', methods=['GET'])
@jwt_required()
def get_all_admins():
    """Получить список всех администраторов"""
    current_admin_id = get_jwt_identity()
    current_admin = Admin.query.get(current_admin_id)
    
    if not current_admin or current_admin.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    admins = Admin.query.all()
    
    return jsonify({
        'admins': [admin.to_dict() for admin in admins]
    })

@auth_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@jwt_required()
def update_admin(admin_id):
    """Обновить данные администратора"""
    current_admin_id = get_jwt_identity()
    current_admin = Admin.query.get(current_admin_id)
    
    if not current_admin:
        return jsonify({'error': 'Администратор не найден'}), 404
    
    # Проверяем права: можно редактировать себя или быть супер-админом
    if current_admin_id != admin_id and current_admin.role != 'super_admin':
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    admin = Admin.query.get_or_404(admin_id)
    data = request.get_json()
    
    try:
        # Обновляем разрешенные поля
        if 'name' in data:
            admin.name = data['name']
        
        if 'email' in data and data['email'] != admin.email:
            # Проверяем уникальность email
            existing = Admin.query.filter_by(email=data['email']).first()
            if existing and existing.id != admin_id:
                return jsonify({'error': 'Email уже используется'}), 400
            admin.email = data['email']
        
        # Только супер-админ может менять роли и статус
        if current_admin.role == 'super_admin':
            if 'role' in data:
                admin.role = data['role']
            if 'active' in data:
                admin.active = data['active']
        
        # Смена пароля
        if 'password' in data and data['password']:
            admin.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'admin': admin.to_dict(),
            'message': 'Данные администратора обновлены'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при обновлении'}), 500

@auth_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@jwt_required()
def delete_admin(admin_id):
    """Удалить администратора"""
    current_admin_id = get_jwt_identity()
    current_admin = Admin.query.get(current_admin_id)
    
    if not current_admin or current_admin.role != 'super_admin':
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    if current_admin_id == admin_id:
        return jsonify({'error': 'Нельзя удалить самого себя'}), 400
    
    admin = Admin.query.get_or_404(admin_id)
    
    try:
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({'message': 'Администратор удален'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при удалении'}), 500