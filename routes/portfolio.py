# routes/portfolio.py
from flask import Blueprint, request, jsonify
from sqlalchemy import desc, func
from models import db, Portfolio, PortfolioView
from datetime import datetime
import logging

portfolio_bp = Blueprint('portfolio', __name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@portfolio_bp.route('/', methods=['GET'])
def get_portfolio():
    """Получить портфолио с фильтрацией и пагинацией"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 12, type=int), 100)
        category = request.args.get('category')
        featured = request.args.get('featured', type=bool)
        status = request.args.get('status', 'published')  # По умолчанию только опубликованные
        
        # Базовый запрос
        query = Portfolio.query
        
        # Фильтр по статусу (для публичного API только published)
        if status:
            query = query.filter(Portfolio.status == status)
        
        # Фильтр по категории
        if category and category != 'all':
            query = query.filter(Portfolio.category == category)
        
        # Фильтр по избранным
        if featured:
            query = query.filter(Portfolio.featured == True)
        
        # Сортировка по дате (новые первыми)
        query = query.order_by(desc(Portfolio.date))
        
        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Формируем ответ
        portfolio_items = [item.to_dict(for_admin=False) for item in pagination.items]
        
        response_data = {
            'portfolio': portfolio_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        logger.info(f"Портфолио загружено: {len(portfolio_items)} элементов, страница {page}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке портфолио: {str(e)}")
        return jsonify({'error': 'Ошибка сервера при загрузке портфолио'}), 500


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
def get_portfolio_item(portfolio_id):
    """Получить детали работы портфолио и увеличить счетчик просмотров"""
    try:
        item = Portfolio.query.get_or_404(portfolio_id)
        
        # Увеличиваем счетчик просмотров
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.environ.get('HTTP_USER_AGENT', '')
        
        view_recorded = item.increment_views(ip_address=ip_address, user_agent=user_agent)
        
        # Получаем связанные работы той же категории
        related_items = Portfolio.query.filter(
            Portfolio.category == item.category,
            Portfolio.id != item.id,
            Portfolio.status == 'published'
        ).limit(4).all()
        
        response_data = {
            'portfolio_item': item.to_dict(for_admin=False),
            'related_items': [item.to_dict(for_admin=False) for item in related_items],
            'view_recorded': view_recorded
        }
        
        logger.info(f"Проект портфолио #{portfolio_id} просмотрен. Новый просмотр: {view_recorded}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке проекта #{portfolio_id}: {str(e)}")
        return jsonify({'error': 'Проект не найден'}), 404


@portfolio_bp.route('/categories', methods=['GET'])
def get_portfolio_categories():
    """Получить категории портфолио с количеством проектов"""
    try:
        # Подсчитываем количество опубликованных проектов по категориям
        categories_data = db.session.query(
            Portfolio.category,
            func.count(Portfolio.id).label('count')
        ).filter(Portfolio.status == 'published').group_by(Portfolio.category).all()
        
        # Общее количество проектов
        total_count = Portfolio.query.filter(Portfolio.status == 'published').count()
        
        # Стандартные названия категорий
        category_names = {
            'children': 'Детские праздники',
            'wedding': 'Свадьбы',
            'corporate': 'Корпоративы',
            'anniversary': 'Юбилеи',
            'show': 'Шоу-программы'
        }
        
        # Формируем список категорий
        categories = [
            {'id': 'all', 'name': 'Все работы', 'count': total_count}
        ]
        
        for category, count in categories_data:
            categories.append({
                'id': category,
                'name': category_names.get(category, category.title()),
                'count': count
            })
        
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке категорий: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500


@portfolio_bp.route('/featured', methods=['GET'])
def get_featured_portfolio():
    """Получить избранные работы портфолио"""
    try:
        limit = request.args.get('limit', 6, type=int)
        
        items = Portfolio.query.filter(
            Portfolio.featured == True,
            Portfolio.status == 'published'
        ).order_by(desc(Portfolio.date)).limit(limit).all()
        
        response_data = {
            'portfolio': [item.to_dict(for_admin=False) for item in items]
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке избранных работ: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500


@portfolio_bp.route('/stats', methods=['GET'])
def get_portfolio_stats():
    """Получить статистику портфолио (для админки)"""
    try:
        stats = Portfolio.get_stats()
        return jsonify({'stats': stats})
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке статистики: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# ADMIN ENDPOINTS (требуют авторизации)

@portfolio_bp.route('/admin', methods=['GET'])
def get_admin_portfolio():
    """Получить все проекты портфолио для админки"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')  # Без фильтра по умолчанию
        category = request.args.get('category')
        
        query = Portfolio.query
        
        if status:
            query = query.filter(Portfolio.status == status)
        
        if category and category != 'all':
            query = query.filter(Portfolio.category == category)
        
        query = query.order_by(desc(Portfolio.created_at))
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'portfolio': [item.to_dict(for_admin=True) for item in pagination.items],
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
        logger.error(f"Ошибка при загрузке портфолио для админки: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500


@portfolio_bp.route('/admin', methods=['POST'])
def create_portfolio_item():
    """Создать новый проект в портфолио"""
    try:
        data = request.get_json()
        
        # Создаем новый проект
        portfolio_item = Portfolio(
            title=data.get('title'),
            category=data.get('category'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else None,
            description=data.get('description'),
            budget=data.get('budget'),
            client=data.get('client'),
            status=data.get('status', 'draft'),
            location=data.get('location'),
            guests=data.get('guests'),
            rating=data.get('rating', 5),
            tags=data.get('tags', []),
            images=data.get('images', []),
            cover_image=data.get('cover_image'),
            packages=data.get('packages', []),
            featured=data.get('featured', False)
        )
        
        # Обновляем количество фото
        if portfolio_item.images:
            portfolio_item.photos_count = len(portfolio_item.images)
        
        db.session.add(portfolio_item)
        db.session.commit()
        
        logger.info(f"Создан новый проект портфолио: {portfolio_item.title}")
        return jsonify({
            'message': 'Проект создан успешно',
            'portfolio_item': portfolio_item.to_dict(for_admin=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании проекта: {str(e)}")
        return jsonify({'error': 'Ошибка при создании проекта'}), 500


@portfolio_bp.route('/admin/<int:portfolio_id>', methods=['PUT'])
def update_portfolio_item(portfolio_id):
    """Обновить проект портфолио"""
    try:
        item = Portfolio.query.get_or_404(portfolio_id)
        data = request.get_json()
        
        # Обновляем поля
        item.title = data.get('title', item.title)
        item.category = data.get('category', item.category)
        item.description = data.get('description', item.description)
        item.budget = data.get('budget', item.budget)
        item.client = data.get('client', item.client)
        item.status = data.get('status', item.status)
        item.location = data.get('location', item.location)
        item.guests = data.get('guests', item.guests)
        item.rating = data.get('rating', item.rating)
        item.tags = data.get('tags', item.tags)
        item.images = data.get('images', item.images)
        item.cover_image = data.get('cover_image', item.cover_image)
        item.packages = data.get('packages', item.packages)
        item.featured = data.get('featured', item.featured)
        
        # Обновляем дату если передана
        if data.get('date'):
            item.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        
        # Обновляем количество фото
        if item.images:
            item.photos_count = len(item.images)
        else:
            item.photos_count = 0
        
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Проект портфолио #{portfolio_id} обновлен")
        return jsonify({
            'message': 'Проект обновлен успешно',
            'portfolio_item': item.to_dict(for_admin=True)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении проекта #{portfolio_id}: {str(e)}")
        return jsonify({'error': 'Ошибка при обновлении проекта'}), 500


@portfolio_bp.route('/admin/<int:portfolio_id>', methods=['DELETE'])
def delete_portfolio_item(portfolio_id):
    """Удалить проект портфолио"""
    try:
        item = Portfolio.query.get_or_404(portfolio_id)
        
        # Удаляем связанные записи просмотров
        PortfolioView.query.filter(PortfolioView.portfolio_id == portfolio_id).delete()
        
        # Удаляем сам проект
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f"Проект портфолио #{portfolio_id} удален")
        return jsonify({'message': 'Проект удален успешно'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении проекта #{portfolio_id}: {str(e)}")
        return jsonify({'error': 'Ошибка при удалении проекта'}), 500


@portfolio_bp.route('/admin/<int:portfolio_id>/views', methods=['GET'])
def get_portfolio_views(portfolio_id):
    """Получить детальную статистику просмотров проекта"""
    try:
        item = Portfolio.query.get_or_404(portfolio_id)
        
        # Получаем записи просмотров
        views = PortfolioView.query.filter(
            PortfolioView.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioView.viewed_at)).limit(100).all()
        
        # Статистика по дням за последние 30 дней
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        daily_views = db.session.query(
            func.date(PortfolioView.viewed_at).label('date'),
            func.count(PortfolioView.id).label('count')
        ).filter(
            PortfolioView.portfolio_id == portfolio_id,
            PortfolioView.viewed_at >= thirty_days_ago
        ).group_by(func.date(PortfolioView.viewed_at)).all()
        
        return jsonify({
            'total_views': item.views,
            'recent_views': [view.to_dict() for view in views],
            'daily_stats': [
                {'date': str(date), 'views': count} 
                for date, count in daily_views
            ]
        })
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке статистики просмотров #{portfolio_id}: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500