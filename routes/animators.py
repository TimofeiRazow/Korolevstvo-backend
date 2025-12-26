from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, func
from models import db, Animator, Admin
from datetime import datetime

animators_bp = Blueprint('animators', __name__)

# ==============================================
# ПУБЛИЧНЫЕ ENDPOINTS
# ==============================================

@animators_bp.route('/', methods=['GET'])
def get_animators():
    """Получить список аниматоров с фильтрацией"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        age_range = request.args.get('age_range')
        popular = request.args.get('popular', type=bool)
        search = request.args.get('search', '').strip()
        
        # Базовый запрос - только активные
        query = Animator.query.filter(Animator.active == True)
        
        # Фильтры
        if category and category != 'all':
            query = query.filter(Animator.category == category)
        
        if age_range:
            query = query.filter(Animator.age_range == age_range)
        
        if popular:
            query = query.filter(Animator.popular == True)
        
        if search:
            query = query.filter(or_(
                Animator.name.contains(search),
                Animator.description.contains(search)
            ))
        
        # Сортировка
        query = query.order_by(Animator.popular.desc(), Animator.name)
        
        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        animators = [animator.to_dict() for animator in pagination.items]
        
        return jsonify({
            'animators': animators,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        print(f"Ошибка получения аниматоров: {e}")
        return jsonify({'error': 'Ошибка получения списка аниматоров'}), 500


@animators_bp.route('/<int:animator_id>', methods=['GET'])
def get_animator(animator_id):
    """Получить одного аниматора по ID"""
    try:
        animator = Animator.query.filter(
            Animator.id == animator_id,
            Animator.active == True
        ).first_or_404()

        return jsonify({'animator': animator.to_dict()})
    except Exception as e:
        print(f"Ошибка получения аниматора: {e}")
        return jsonify({'error': 'Аниматор не найден'}), 404


@animators_bp.route('/<int:animator_id>', methods=['POST'])
def increment_animator_views(animator_id):
    """Увеличить счетчик просмотров аниматора"""
    try:
        animator = Animator.query.filter(
            Animator.id == animator_id,
            Animator.active == True
        ).first_or_404()

        animator.increment_views()

        return jsonify({
            'success': True,
            'views_count': animator.views_count
        })
    except Exception as e:
        print(f"Ошибка увеличения просмотров: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@animators_bp.route('/slug/<slug>', methods=['GET'])
def get_animator_by_slug(slug):
    """Получить аниматора по slug"""
    try:
        animator = Animator.get_by_slug(slug, active_only=True)
        if not animator:
            return jsonify({'error': 'Аниматор не найден'}), 404
        
        # Увеличиваем счетчик просмотров
        animator.increment_views()
        
        return jsonify({'animator': animator.to_dict()})
    except Exception as e:
        print(f"Ошибка получения аниматора по slug: {e}")
        return jsonify({'error': 'Ошибка получения аниматора'}), 500


@animators_bp.route('/popular', methods=['GET'])
def get_popular_animators():
    """Получить популярных аниматоров"""
    try:
        limit = request.args.get('limit', 6, type=int)
        animators = Animator.get_popular(limit=limit, active_only=True)
        
        return jsonify({
            'animators': [animator.to_dict() for animator in animators]
        })
    except Exception as e:
        print(f"Ошибка получения популярных аниматоров: {e}")
        return jsonify({'error': 'Ошибка получения аниматоров'}), 500


@animators_bp.route('/category/<category>', methods=['GET'])
def get_animators_by_category(category):
    """Получить аниматоров по категории"""
    try:
        animators = Animator.get_by_category(category, active_only=True)
        
        return jsonify({
            'category': category,
            'animators': [animator.to_dict() for animator in animators]
        })
    except Exception as e:
        print(f"Ошибка получения аниматоров по категории: {e}")
        return jsonify({'error': 'Ошибка получения аниматоров'}), 500


@animators_bp.route('/search', methods=['GET'])
def search_animators():
    """Поиск аниматоров"""
    try:
        query_text = request.args.get('q', '').strip()
        if not query_text:
            return jsonify({'error': 'Пустой поисковый запрос'}), 400

        animators = Animator.search(query_text, active_only=True)

        return jsonify({
            'query': query_text,
            'results': [animator.to_dict() for animator in animators]
        })
    except Exception as e:
        print(f"Ошибка поиска аниматоров: {e}")
        return jsonify({'error': 'Ошибка поиска'}), 500


@animators_bp.route('/categories', methods=['GET'])
def get_categories():
    """Получить список категорий аниматоров"""
    try:
        # Получаем уникальные категории из активных аниматоров
        categories_raw = db.session.query(
            Animator.category,
            func.count(Animator.id).label('count')
        ).filter(
            Animator.active == True
        ).group_by(Animator.category).all()

        # Словарь с читаемыми названиями категорий
        category_names = {
            'superheroes': 'Супергерои',
            'princesses': 'Принцессы',
            'cartoons': 'Мультяшки',
            'themed': 'Тематические',
            'animals': 'Животные',
            'fairy_tales': 'Сказочные',
            'games': 'Игровые'
        }

        categories = []
        for category, count in categories_raw:
            categories.append({
                'id': category,
                'name': category_names.get(category, category.capitalize()),
                'count': count
            })

        return jsonify({'categories': categories})
    except Exception as e:
        print(f"Ошибка получения категорий: {e}")
        return jsonify({'error': 'Ошибка получения категорий'}), 500


# ==============================================
# АДМИНСКИЕ ENDPOINTS
# ==============================================

@animators_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_admin_animators():
    """Получить все аниматоры для админки (включая неактивные)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        active = request.args.get('active')
        popular = request.args.get('popular')
        search = request.args.get('search', '').strip()
        
        # Базовый запрос без фильтра по active
        query = Animator.query
        
        # Фильтры
        if category and category != 'all':
            query = query.filter(Animator.category == category)
        
        if active is not None:
            query = query.filter(Animator.active == (active.lower() == 'true'))
        
        if popular is not None:
            query = query.filter(Animator.popular == (popular.lower() == 'true'))
        
        if search:
            query = query.filter(or_(
                Animator.name.contains(search),
                Animator.description.contains(search),
                Animator.category.contains(search)
            ))
        
        # Сортировка
        query = query.order_by(Animator.created_at.desc())
        
        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        animators = [animator.to_dict(include_sensitive=True) for animator in pagination.items]
        
        return jsonify({
            'animators': animators,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        print(f"Ошибка получения аниматоров для админки: {e}")
        return jsonify({'error': 'Ошибка получения списка аниматоров'}), 500


@animators_bp.route('/admin', methods=['POST'])
@jwt_required()
def create_animator():
    """Создать нового аниматора"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Валидация обязательных полей
        required_fields = ['name', 'title', 'category', 'age_range', 'description', 'price', 'duration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле {field} обязательно'}), 400
        
        # Проверка уникальности slug
        if 'slug' in data and data['slug']:
            existing = Animator.query.filter(Animator.slug == data['slug']).first()
            if existing:
                return jsonify({'error': 'Аниматор с таким slug уже существует'}), 409
        
        # Создаем аниматора
        animator = Animator(
            name=data['name'].strip(),
            title=data['title'].strip(),
            category=data['category'],
            age_range=data['age_range'],
            description=data['description'],
            price=data['price'],
            duration=data['duration']
        )
        
        # Дополнительные поля
        if 'program_includes' in data:
            animator.program_includes = data['program_includes']
        if 'suitable_for' in data:
            animator.suitable_for = data['suitable_for']
        if 'advantages' in data:
            animator.advantages = data['advantages']
        if 'related_characters' in data:
            animator.related_characters = data['related_characters']
        if 'image' in data:
            animator.image = data['image']
        if 'popular' in data:
            animator.popular = bool(data['popular'])
        if 'active' in data:
            animator.active = bool(data['active'])
        if 'meta_title' in data:
            animator.meta_title = data['meta_title']
        if 'meta_description' in data:
            animator.meta_description = data['meta_description']
        if 'meta_keywords' in data:
            animator.meta_keywords = data['meta_keywords']
        
        db.session.add(animator)
        db.session.commit()
        
        return jsonify({
            'message': 'Аниматор успешно создан',
            'animator': animator.to_dict(include_sensitive=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка создания аниматора: {e}")
        return jsonify({'error': 'Ошибка при создании аниматора'}), 500


@animators_bp.route('/admin/<int:animator_id>', methods=['PUT'])
@jwt_required()
def update_animator(animator_id):
    """Обновить аниматора"""
    try:
        animator = Animator.query.get_or_404(animator_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Проверка уникальности slug при изменении
        if 'slug' in data and data['slug'] != animator.slug:
            existing = Animator.query.filter(Animator.slug == data['slug']).first()
            if existing:
                return jsonify({'error': 'Аниматор с таким slug уже существует'}), 409
        
        # Обновляем поля
        animator.update_from_dict(data)
        db.session.commit()
        
        return jsonify({
            'message': 'Аниматор успешно обновлен',
            'animator': animator.to_dict(include_sensitive=True)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка обновления аниматора: {e}")
        return jsonify({'error': 'Ошибка при обновлении аниматора'}), 500


@animators_bp.route('/admin/<int:animator_id>', methods=['DELETE'])
@jwt_required()
def delete_animator(animator_id):
    """Удалить аниматора"""
    try:
        animator = Animator.query.get_or_404(animator_id)
        name = animator.name
        
        db.session.delete(animator)
        db.session.commit()
        
        return jsonify({
            'message': f'Аниматор "{name}" успешно удален'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка удаления аниматора: {e}")
        return jsonify({'error': 'Ошибка при удалении аниматора'}), 500


@animators_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_animators_stats():
    """Получить статистику по аниматорам для админки"""
    try:
        stats = Animator.get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        return jsonify({'error': 'Ошибка получения статистики'}), 500


@animators_bp.route('/admin/<int:animator_id>/toggle-popular', methods=['PATCH'])
@jwt_required()
def toggle_popular(animator_id):
    """Переключить статус популярности"""
    try:
        animator = Animator.query.get_or_404(animator_id)
        animator.popular = not animator.popular
        db.session.commit()
        
        return jsonify({
            'message': f'Статус популярности изменен',
            'popular': animator.popular
        })
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка изменения статуса: {e}")
        return jsonify({'error': 'Ошибка изменения статуса'}), 500


@animators_bp.route('/admin/<int:animator_id>/toggle-active', methods=['PATCH'])
@jwt_required()
def toggle_active(animator_id):
    """Переключить активность аниматора"""
    try:
        animator = Animator.query.get_or_404(animator_id)
        animator.active = not animator.active
        db.session.commit()
        
        return jsonify({
            'message': f'Статус активности изменен',
            'active': animator.active
        })
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка изменения статуса: {e}")
        return jsonify({'error': 'Ошибка изменения статуса'}), 500