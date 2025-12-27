# routes/shows.py - API для шоу-программ
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, func
from models import db, Show, Admin
from datetime import datetime

shows_bp = Blueprint('shows', __name__)

# ПУБЛИЧНЫЕ МАРШРУТЫ

@shows_bp.route('/', methods=['GET', 'OPTIONS'])
def get_shows():
    """Получить список шоу-программ с фильтрацией и пагинацией"""
    if request.method == "OPTIONS":
        return '', 204

    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        featured = request.args.get('featured', type=bool)
        search = request.args.get('search', '').strip()
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Базовый запрос
        query = Show.query

        # Фильтры
        if category and category != 'all':
            query = query.filter(Show.category == category)

        if featured:
            query = query.filter(Show.featured == True)

        if status:
            query = query.filter(Show.status == status)
        else:
            # По умолчанию показываем только активные шоу для публичного API
            query = query.filter(Show.status == 'active')

        if search:
            query = query.filter(or_(
                Show.title.contains(search),
                Show.description.contains(search)
            ))

        # Сортировка
        sort_column = getattr(Show, sort_by, Show.created_at)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        shows = [show.to_dict() for show in pagination.items]

        return jsonify({
            'shows': shows,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': pagination.next_num if pagination.has_next else None,
                'prev_page': pagination.prev_num if pagination.has_prev else None
            }
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка при получении шоу: {str(e)}'}), 500


@shows_bp.route('/<int:show_id>', methods=['GET'])
def get_show(show_id):
    """Получить детали шоу-программы"""
    try:
        show = Show.query.get_or_404(show_id)

        # Увеличиваем счетчик просмотров
        show.increment_views()

        # Получить связанные шоу той же категории
        related_shows = Show.query.filter(
            and_(
                Show.category == show.category,
                Show.id != show.id,
                Show.status == 'active'
            )
        ).limit(4).all()

        return jsonify({
            'show': show.to_dict(),
            'related': [s.to_dict() for s in related_shows]
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка при получении шоу: {str(e)}'}), 500


@shows_bp.route('/categories', methods=['GET'])
def get_categories():
    """Получить список категорий шоу с количеством"""
    try:
        categories_data = db.session.query(
            Show.category,
            func.count(Show.id).label('count')
        ).filter(Show.status == 'active').group_by(Show.category).all()

        category_names = {
            'fire': 'Огненные шоу',
            'music': 'Музыкальные',
            'dance': 'Танцевальные',
            'magic': 'Фокусы',
            'acrobatic': 'Акробатика',
            'light': 'Световые'
        }

        categories = [{
            'id': 'all',
            'name': 'Все шоу',
            'count': Show.query.filter(Show.status == 'active').count()
        }]

        for category, count in categories_data:
            categories.append({
                'id': category,
                'name': category_names.get(category, category.title()),
                'count': count
            })

        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': f'Ошибка при получении категорий: {str(e)}'}), 500


@shows_bp.route('/featured', methods=['GET'])
def get_featured_shows():
    """Получить популярные шоу"""
    try:
        limit = request.args.get('limit', 6, type=int)
        shows = Show.get_featured(limit=limit)

        return jsonify({
            'shows': [show.to_dict() for show in shows]
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка при получении популярных шоу: {str(e)}'}), 500


# АДМИНИСТРАТИВНЫЕ МАРШРУТЫ

@shows_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_admin_shows():
    """Получить все шоу для админки (включая неактивные)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Базовый запрос без фильтра статуса
        query = Show.query

        # Фильтры
        if category and category != 'all':
            query = query.filter(Show.category == category)

        if status and status != 'all':
            query = query.filter(Show.status == status)

        if search:
            query = query.filter(or_(
                Show.title.contains(search),
                Show.description.contains(search),
                Show.category.contains(search)
            ))

        # Сортировка
        sort_column = getattr(Show, sort_by, Show.created_at)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        shows = [show.to_dict() for show in pagination.items]

        return jsonify({
            'shows': shows,
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
        return jsonify({'error': f'Ошибка при получении шоу: {str(e)}'}), 500


@shows_bp.route('/admin', methods=['POST'])
@jwt_required()
def create_show():
    """Создать новое шоу"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Нет данных'}), 400

        # Валидация обязательных полей
        required_fields = ['title', 'category', 'description', 'duration', 'minAudience', 'price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле {field} обязательно'}), 400

        # Создаем новое шоу
        show = Show(
            title=data.get('title'),
            category=data.get('category'),
            duration=data.get('duration'),
            min_audience=data.get('minAudience'),
            rating=float(data.get('rating', 5.0)),
            price=data.get('price'),
            price_description=data.get('priceDescription'),
            description=data.get('description'),
            features=data.get('features', []),
            suitable_for=data.get('suitableFor', []),
            cover_image=data.get('coverImage'),
            images=data.get('images', []),
            videos=data.get('videos', []),
            featured=data.get('featured', False),
            tags=data.get('tags', []),
            status=data.get('status', 'active')
        )

        db.session.add(show)
        db.session.commit()

        return jsonify({
            'message': 'Шоу успешно создано',
            'show': show.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при создании шоу: {str(e)}'}), 500


@shows_bp.route('/admin/<int:show_id>', methods=['PUT'])
@jwt_required()
def update_show(show_id):
    """Обновить шоу"""
    try:
        show = Show.query.get_or_404(show_id)
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Нет данных'}), 400

        # Обновляем шоу через метод модели
        show.update_from_dict(data)
        db.session.commit()

        return jsonify({
            'message': 'Шоу успешно обновлено',
            'show': show.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при обновлении шоу: {str(e)}'}), 500


@shows_bp.route('/admin/<int:show_id>', methods=['DELETE'])
@jwt_required()
def delete_show(show_id):
    """Удалить шоу"""
    try:
        show = Show.query.get_or_404(show_id)

        db.session.delete(show)
        db.session.commit()

        return jsonify({'message': 'Шоу успешно удалено'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при удалении шоу: {str(e)}'}), 500


@shows_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_shows_stats():
    """Получить статистику шоу для админки"""
    try:
        stats = Show.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Ошибка при получении статистики: {str(e)}'}), 500


@shows_bp.route('/admin/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_shows():
    """Массовое обновление шоу"""
    try:
        data = request.get_json()
        show_ids = data.get('show_ids', [])
        update_data = data.get('update_data', {})

        if not show_ids or not update_data:
            return jsonify({'error': 'Не указаны шоу или данные для обновления'}), 400

        shows = Show.query.filter(Show.id.in_(show_ids)).all()

        for show in shows:
            if 'status' in update_data:
                show.status = update_data['status']
            if 'featured' in update_data:
                show.featured = update_data['featured']
            if 'category' in update_data:
                show.category = update_data['category']

        db.session.commit()

        return jsonify({
            'message': f'Обновлено {len(shows)} шоу',
            'updated_count': len(shows)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при массовом обновлении: {str(e)}'}), 500


@shows_bp.route('/admin/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_shows():
    """Массовое удаление шоу"""
    try:
        data = request.get_json()
        show_ids = data.get('show_ids', [])

        if not show_ids:
            return jsonify({'error': 'Не указаны шоу для удаления'}), 400

        deleted_count = Show.query.filter(Show.id.in_(show_ids)).delete(synchronize_session=False)
        db.session.commit()

        return jsonify({
            'message': f'Удалено {deleted_count} шоу',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при массовом удалении: {str(e)}'}), 500
