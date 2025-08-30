# routes/blog.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, BlogPost, Admin, BlogView
from utils.validators import validate_blog_post
from utils.helpers import get_client_ip, paginate_query
from datetime import datetime
import logging

blog_bp = Blueprint('blog', __name__)

# Публичные маршруты (не требуют авторизации)

@blog_bp.route('/', methods=['GET'])
def get_blog_posts():
    """Получить опубликованные статьи блога с пагинацией и фильтрами"""
    try:
        # Параметры запроса
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 12, type=int), 50)
        category = request.args.get('category')
        featured = request.args.get('featured', type=bool)
        tags = request.args.get('tags')  # Строка тегов через запятую
        search = request.args.get('search')
        
        # Базовый запрос - только опубликованные статьи
        query = BlogPost.query.filter(BlogPost.status == 'published')
        
        # Применяем фильтры
        if category:
            query = query.filter(BlogPost.category == category)
        
        if featured is not None:
            query = query.filter(BlogPost.featured == featured)
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                query = query.filter(BlogPost.tags.contains([tag]))
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    BlogPost.title.ilike(search_filter),
                    BlogPost.excerpt.ilike(search_filter),
                    BlogPost.content.ilike(search_filter)
                )
            )
        
        # Сортировка по дате публикации
        query = query.order_by(BlogPost.published_at.desc())
        
        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        posts = [post.to_dict(include_content=False) for post in pagination.items]
        
        return jsonify({
            'posts': posts,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting blog posts: {e}")
        return jsonify({'error': 'Ошибка загрузки статей'}), 500


@blog_bp.route('/<slug>', methods=['GET'])
def get_blog_post_by_slug(slug):
    """Получить статью по slug"""
    try:
        post = BlogPost.get_by_slug(slug)
        
        if not post:
            return jsonify({'error': 'Статья не найдена'}), 404
        
        # Увеличиваем счетчик просмотров
        client_ip = get_client_ip(request)
        user_agent = request.headers.get('User-Agent', '')
        post.increment_views(client_ip, user_agent)
        
        # Получаем похожие статьи (по категории)
        related_posts = BlogPost.query.filter(
            BlogPost.status == 'published',
            BlogPost.category == post.category,
            BlogPost.id != post.id
        ).order_by(BlogPost.published_at.desc()).limit(3).all()
        
        return jsonify({
            'post': post.to_dict(include_content=True),
            'related_posts': [p.to_dict(include_content=False) for p in related_posts]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting blog post by slug {slug}: {e}")
        return jsonify({'error': 'Ошибка загрузки статьи'}), 500


@blog_bp.route('/categories', methods=['GET'])
def get_blog_categories():
    """Получить список категорий блога"""
    try:
        categories = db.session.query(
            BlogPost.category,
            db.func.count(BlogPost.id).label('count')
        ).filter(
            BlogPost.status == 'published'
        ).group_by(BlogPost.category).all()
        
        category_list = [
            {'name': cat, 'count': count, 'slug': cat.lower().replace(' ', '-')}
            for cat, count in categories
        ]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        logging.error(f"Error getting blog categories: {e}")
        return jsonify({'error': 'Ошибка загрузки категорий'}), 500


@blog_bp.route('/featured', methods=['GET'])
def get_featured_posts():
    """Получить избранные статьи"""
    try:
        limit = min(request.args.get('limit', 6, type=int), 20)
        
        posts = BlogPost.get_published(limit=limit, featured=True)
        
        return jsonify({
            'posts': [post.to_dict(include_content=False) for post in posts]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting featured posts: {e}")
        return jsonify({'error': 'Ошибка загрузки избранных статей'}), 500


@blog_bp.route('/latest', methods=['GET'])
def get_latest_posts():
    """Получить последние статьи"""
    try:
        limit = min(request.args.get('limit', 5, type=int), 20)
        
        posts = BlogPost.get_published(limit=limit)
        
        return jsonify({
            'posts': [post.to_dict(include_content=False) for post in posts]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting latest posts: {e}")
        return jsonify({'error': 'Ошибка загрузки последних статей'}), 500


@blog_bp.route('/search', methods=['GET'])
def search_blog_posts():
    """Поиск по статьям блога"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Минимальная длина запроса: 2 символа'}), 400
        
        posts = BlogPost.search(query, limit)
        
        return jsonify({
            'posts': [post.to_dict(include_content=False) for post in posts],
            'query': query,
            'total': len(posts)
        }), 200
        
    except Exception as e:
        logging.error(f"Error searching blog posts: {e}")
        return jsonify({'error': 'Ошибка поиска'}), 500


@blog_bp.route('/stats', methods=['GET'])
def get_blog_stats():
    """Получить публичную статистику блога"""
    try:
        stats = BlogPost.get_stats()
        
        # Возвращаем только публичную статистику
        return jsonify({
            'published': stats['published'],
            'categories': stats['categories'],
            'total_views': stats['total_views']
        }), 200
        
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        return jsonify({'error': 'Ошибка загрузки статистики'}), 500


# Административные маршруты (требуют авторизации)

@blog_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_admin_blog_posts():
    """Получить все статьи для админки"""
    try:
        # Параметры запроса
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')  # draft, published, scheduled, archived
        category = request.args.get('category')
        author_id = request.args.get('author_id', type=int)
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Базовый запрос
        query = BlogPost.query
        
        # Применяем фильтры
        if status:
            query = query.filter(BlogPost.status == status)
        
        if category:
            query = query.filter(BlogPost.category == category)
        
        if author_id:
            query = query.filter(BlogPost.author_id == author_id)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    BlogPost.title.ilike(search_filter),
                    BlogPost.content.ilike(search_filter)
                )
            )
        
        # Сортировка
        sort_column = getattr(BlogPost, sort_by, BlogPost.updated_at)
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
        
        posts = [post.to_dict(include_content=True, for_admin=True) for post in pagination.items]
        return jsonify({
            'posts': posts,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting admin blog posts: {e}")
        return jsonify({'error': 'Ошибка загрузки статей'}), 500


@blog_bp.route('/admin', methods=['POST'])
@jwt_required()
def create_blog_post():
    """Создать новую статью"""
    try:
        current_admin_id = get_jwt_identity()
        admin = Admin.query.get(current_admin_id)
        
        if not admin:
            return jsonify({'error': 'Администратор не найден'}), 404
        
        data = request.get_json()
        
        # Валидация данных
        is_valid, errors = validate_blog_post(data)
        if not is_valid:
            return jsonify({'error': 'Ошибка валидации', 'details': errors}), 400
        
        # Проверяем уникальность slug
        if data.get('slug'):
            existing_post = BlogPost.query.filter(BlogPost.slug == data['slug']).first()
            if existing_post:
                return jsonify({'error': 'Статья с таким URL уже существует'}), 400
        
        # Создаем новую статью
        post = BlogPost(
            author_id=current_admin_id,
            author_name=data.get('author_name', admin.name)
        )
        
        post.update_from_dict(data)
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Статья успешно создана',
            'post': post.to_dict(for_admin=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating blog post: {e}")
        return jsonify({'error': 'Ошибка создания статьи'}), 500


@blog_bp.route('/admin/<int:post_id>', methods=['GET'])
@jwt_required()
def get_admin_blog_post(post_id):
    """Получить статью для редактирования"""
    try:
        post = BlogPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Статья не найдена'}), 404
        
        return jsonify({
            'post': post.to_dict(include_content=True, for_admin=True)
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting admin blog post {post_id}: {e}")
        return jsonify({'error': 'Ошибка загрузки статьи'}), 500


@blog_bp.route('/admin/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_blog_post(post_id):
    """Обновить статью"""
    try:
        post = BlogPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Статья не найдена'}), 404
        
        data = request.get_json()
        
        # Валидация данных
        is_valid, errors = validate_blog_post(data, is_update=True)
        if not is_valid:
            return jsonify({'error': 'Ошибка валидации', 'details': errors}), 400
        
        # Проверяем уникальность slug (если изменился)
        if data.get('slug') and data['slug'] != post.slug:
            existing_post = BlogPost.query.filter(
                BlogPost.slug == data['slug'],
                BlogPost.id != post_id
            ).first()
            if existing_post:
                return jsonify({'error': 'Статья с таким URL уже существует'}), 400
        
        # Обновляем статью
        post.update_from_dict(data)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Статья успешно обновлена',
            'post': post.to_dict(for_admin=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating blog post {post_id}: {e}")
        return jsonify({'error': 'Ошибка обновления статьи'}), 500


@blog_bp.route('/admin/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_blog_post(post_id):
    """Удалить статью"""
    try:
        post = BlogPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Статья не найдена'}), 404
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Статья успешно удалена'}), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting blog post {post_id}: {e}")
        return jsonify({'error': 'Ошибка удаления статьи'}), 500


@blog_bp.route('/admin/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_blog_posts():
    """Массовое удаление статей"""
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', [])
        
        if not post_ids:
            return jsonify({'error': 'Не указаны ID статей для удаления'}), 400
        
        # Находим статьи для удаления
        posts = BlogPost.query.filter(BlogPost.id.in_(post_ids)).all()
        
        if not posts:
            return jsonify({'error': 'Статьи не найдены'}), 404
        
        deleted_count = len(posts)
        
        # Удаляем статьи
        for post in posts:
            db.session.delete(post)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Удалено статей: {deleted_count}',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting blog posts: {e}")
        return jsonify({'error': 'Ошибка массового удаления статей'}), 500


@blog_bp.route('/admin/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_blog_posts():
    """Массовое обновление статей"""
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', [])
        update_data = data.get('update_data', {})
        
        if not post_ids:
            return jsonify({'error': 'Не указаны ID статей для обновления'}), 400
        
        if not update_data:
            return jsonify({'error': 'Не указаны данные для обновления'}), 400
        
        # Находим статьи для обновления
        posts = BlogPost.query.filter(BlogPost.id.in_(post_ids)).all()
        
        if not posts:
            return jsonify({'error': 'Статьи не найдены'}), 404
        
        updated_count = 0
        
        # Обновляем статьи
        for post in posts:
            if 'status' in update_data:
                post.status = update_data['status']
                if update_data['status'] == 'published' and not post.published_at:
                    post.published_at = datetime.utcnow()
            
            if 'featured' in update_data:
                post.featured = bool(update_data['featured'])
            
            if 'category' in update_data:
                post.category = update_data['category']
            
            post.updated_at = datetime.utcnow()
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Обновлено статей: {updated_count}',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk updating blog posts: {e}")
        return jsonify({'error': 'Ошибка массового обновления статей'}), 500


@blog_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_blog_stats():
    """Получить полную статистику блога для админки"""
    try:
        # Основная статистика
        stats = BlogPost.get_stats()
        
        # Статистика по авторам
        authors = db.session.query(
            BlogPost.author_name,
            db.func.count(BlogPost.id).label('count')
        ).group_by(BlogPost.author_name).all()
        
        # Статистика по месяцам (используем новый метод)
        monthly_stats = BlogPost.get_monthly_stats(limit_months=12)
        
        # Топ статей по просмотрам
        top_posts = BlogPost.get_top_posts(limit=10, by_views=True)
        
        # Последние статьи
        recent_posts = BlogPost.get_top_posts(limit=5, by_views=False)
        
        return jsonify({
            **stats,
            'authors': [{'name': name, 'count': count} for name, count in authors],
            'monthly_stats': monthly_stats,
            'top_posts': top_posts,
            'recent_posts': recent_posts
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting admin blog stats: {e}")
        return jsonify({'error': 'Ошибка загрузки статистики'}), 500


@blog_bp.route('/admin/export', methods=['GET'])
@jwt_required()
def export_blog_posts():
    """Экспорт статей в CSV"""
    try:
        import csv
        import io
        
        # Параметры фильтрации
        status = request.args.get('status')
        category = request.args.get('category')
        author_id = request.args.get('author_id', type=int)
        
        # Базовый запрос
        query = BlogPost.query
        
        if status:
            query = query.filter(BlogPost.status == status)
        if category:
            query = query.filter(BlogPost.category == category)
        if author_id:
            query = query.filter(BlogPost.author_id == author_id)
        
        posts = query.order_by(BlogPost.created_at.desc()).all()
        
        # Создаем CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID', 'Заголовок', 'Slug', 'Категория', 'Автор', 'Статус',
            'Избранная', 'Просмотры', 'Дата создания', 'Дата публикации'
        ])
        
        # Данные
        for post in posts:
            writer.writerow([
                post.id,
                post.title,
                post.slug,
                post.category,
                post.author_name,
                post.status,
                'Да' if post.featured else 'Нет',
                post.views_count,
                post.created_at.strftime('%Y-%m-%d %H:%M'),
                post.published_at.strftime('%Y-%m-%d %H:%M') if post.published_at else ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=blog_posts_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
    except Exception as e:
        logging.error(f"Error exporting blog posts: {e}")
        return jsonify({'error': 'Ошибка экспорта статей'}), 500


# Дополнительные утилиты
def register_blog_routes(app):
    """Регистрация маршрутов блога"""
    app.register_blueprint(blog_bp, url_prefix='/api/blog')