# routes/warehouse.py - Полностью обновленные эндпоинты
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, func, or_, and_
from models import db, WarehouseItem, WarehouseCategory, WarehouseOperation, Admin, WarehouseItemCategory
from utils.barcode import get_product_from_service_online
from datetime import datetime, timedelta
import csv
import io
import json
import requests
from utils.helpers import get_client_ip

warehouse_bp = Blueprint('warehouse', __name__)

# ============ DASHBOARD / ГЛАВНАЯ ============

@warehouse_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_warehouse_dashboard():
    """Получить данные для главной страницы склада"""
    try:
        from models import get_warehouse_stats
        stats = get_warehouse_stats()
        
        # Последние операции
        recent_operations = WarehouseOperation.query.order_by(
            desc(WarehouseOperation.created_at)
        ).limit(10).all()
        
        # Товары с низким остатком
        low_stock_items = WarehouseItem.get_low_stock_items()
        
        # Самые активные товары за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_items = db.session.query(
            WarehouseItem.id,
            WarehouseItem.name,
            func.count(WarehouseOperation.id).label('operation_count')
        ).join(WarehouseOperation).filter(
            WarehouseOperation.created_at >= thirty_days_ago
        ).group_by(WarehouseItem.id).order_by(
            desc(func.count(WarehouseOperation.id))
        ).limit(5).all()
        
        return jsonify({
            'stats': stats,
            'recent_operations': [op.to_dict() for op in recent_operations],
            'low_stock_items': [item.to_dict() for item in low_stock_items[:5]],
            'active_items': [
                {
                    'id': item_id,
                    'name': name,
                    'operation_count': count
                }
                for item_id, name, count in active_items
            ]
        })
        
    except Exception as e:
        print(f"❌ Ошибка dashboard: {e}")
        return jsonify({'error': f'Ошибка получения данных: {str(e)}'}), 500


# ============ КАТЕГОРИИ ============

@warehouse_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Получить список категорий с поддержкой множественных товаров"""
    try:
        parent_id = request.args.get('parent_id', type=int)
        include_children = request.args.get('include_children', 'true').lower() == 'true'
        
        print(f"📂 GET categories: parent_id={parent_id}, include_children={include_children}")
        
        query = WarehouseCategory.query
        
        if parent_id is not None:
            query = query.filter(WarehouseCategory.parent_id == parent_id)
        else:
            query = query.filter(WarehouseCategory.parent_id.is_(None))
        
        categories = query.order_by(WarehouseCategory.name).all()
        
        # Добавляем информацию о количестве товаров в каждой категории
        result = []
        for category in categories:
            try:
                cat_data = category.to_dict(include_children=include_children)
                
                # Подсчитываем товары в категории (включая подкатегории) через связь many-to-many
                category_ids = [category.id]
                if include_children:
                    category_ids.extend(category.get_all_child_ids())
                
                items_count = db.session.query(WarehouseItem).join(WarehouseItemCategory).filter(
                    WarehouseItemCategory.category_id.in_(category_ids),
                    WarehouseItem.status == 'active'
                ).distinct().count()
                
                cat_data['items_count'] = items_count
                result.append(cat_data)
                
            except Exception as e:
                print(f"❌ Ошибка обработки категории {category.id}: {e}")
                # Добавляем категорию с базовой информацией
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'items_count': 0,
                    'error': str(e)
                })
        
        print(f"✅ Возвращаем {len(result)} категорий")
        return jsonify({'categories': result})
        
    except Exception as e:
        print(f"❌ Критическая ошибка get_categories: {e}")
        return jsonify({'error': f'Ошибка получения категорий: {str(e)}'}), 500


@warehouse_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Создать новую категорию"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Название категории обязательно'}), 400
        
        category = WarehouseCategory(
            name=data['name'].strip(),
            parent_id=data.get('parent_id'),
            description=data.get('description', '').strip(),
            color=data.get('color', '#6366f1')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Категория создана успешно',
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка создания категории: {str(e)}'}), 500


@warehouse_bp.route('/categories/search', methods=['GET'])
@jwt_required()
def search_categories():
    """Поиск категорий для автодополнения"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        if not query:
            return jsonify({'categories': []})
        
        search_filter = f"%{query}%"
        from sqlalchemy import func

        categories = WarehouseCategory.query.filter(
            func.lower(WarehouseCategory.name).like(func.lower(search_filter))
        ).limit(limit).all()
        
        return jsonify({
            'categories': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'full_path': cat.get_full_path()
                }
                for cat in categories
            ]
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка поиска категорий: {str(e)}'}), 500


# ============ ТОВАРЫ ============

@warehouse_bp.route('/items', methods=['POST'])
@jwt_required()
def create_item():
    """Создать новый товар с поддержкой множественных категорий"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        print(f"📦 POST /items - создание товара: {data.get('name', 'Без названия')}")
        
        # Валидация обязательных полей
        required_fields = ['name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле {field} обязательно'}), 400
        
        # Проверяем уникальность штрих-кода
        if data.get('barcode'):
            existing_item = WarehouseItem.query.filter(
                WarehouseItem.barcode == data['barcode']
            ).first()
            if existing_item:
                return jsonify({'error': 'Товар с таким штрих-кодом уже существует'}), 400
        
        # Проверяем уникальность SKU
        if data.get('sku'):
            existing_item = WarehouseItem.query.filter(
                WarehouseItem.sku == data['sku']
            ).first()
            if existing_item:
                return jsonify({'error': 'Товар с таким артикулом уже существует'}), 400
        
        # Создаем товар
        item = WarehouseItem(
            name=data['name'].strip(),
            barcode=data.get('barcode', '').strip() or None,
            sku=data.get('sku', '').strip() or None,
            description=data.get('description', '').strip(),
            unit=data.get('unit', 'шт').strip(),
            min_quantity=data.get('min_quantity', 0),
            max_quantity=data.get('max_quantity', 1000),
            cost_price=data.get('cost_price', 0),
            current_quantity=data.get('current_quantity', 0)
        )
        
        db.session.add(item)
        db.session.flush()  # Получаем ID товара
        
        # Обработка категорий
        category_ids = []
        
        # Различные способы передачи категорий
        if data.get('category_id'):
            category_ids.append(data['category_id'])
        
        if data.get('category_ids'):
            category_ids.extend(data['category_ids'])
        
        if data.get('category_names'):
            for category_name in data['category_names']:
                if category_name and category_name.strip():
                    category = WarehouseCategory.find_or_create_by_name(
                        name=category_name.strip()
                    )
                    category_ids.append(category.id)
        
        if data.get('category_name'):
            category = WarehouseCategory.find_or_create_by_name(
                name=data['category_name'].strip()
            )
            category_ids.append(category.id)
        
        # selectedCategories из фронтенда (AddItemModal)
        if data.get('selectedCategories'):
            for category_name in data['selectedCategories']:
                if category_name and category_name.strip():
                    category = WarehouseCategory.find_or_create_by_name(
                        name=category_name.strip()
                    )
                    category_ids.append(category.id)
        
        # Убираем дублирующиеся ID
        category_ids = list(set(category_ids))
        
        # Если категории указаны, добавляем связи
        if category_ids:
            item.set_categories(category_ids)
            print(f"🏷️ Добавлены категории: {category_ids}")
        else:
            # Если категории не указаны, создаем категорию "Без категории"
            default_category = WarehouseCategory.find_or_create_by_name("Без категории")
            item.set_categories([default_category.id])
            print(f"🏷️ Добавлена категория по умолчанию: {default_category.id}")
        
        # Если указано начальное количество, создаем операцию поступления
        initial_quantity = data.get('current_quantity', 0)
        if initial_quantity > 0:
            operation = WarehouseOperation(
                item_id=item.id,
                operation_type='add',
                quantity_before=0,
                quantity_after=initial_quantity,
                quantity_change=initial_quantity,
                reason='Начальный остаток',
                user_id=current_user_id,
                ip_address=get_client_ip(request)
            )
            db.session.add(operation)
        
        db.session.commit()
        
        print(f"✅ Товар создан: ID {item.id}")
        return jsonify({
            'message': 'Товар создан успешно',
            'item': item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка создания товара: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка создания товара: {str(e)}'}), 500


@warehouse_bp.route('/items', methods=['GET'])
@jwt_required()
def get_items():
    """Получить список товаров с поддержкой множественных категорий"""
    try:
        # Получение параметров запроса
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Поддержка как старого, так и нового формата категорий
        category_ids = request.args.getlist('category_ids')  # Новый формат - множественные
        category_id = request.args.get('category_id', type=int)  # Старый формат - одна категория
        
        search = request.args.get('search', '').strip()
        status = request.args.get('status', 'active')
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        stock_filter = request.args.get('stock_filter')
        
        print(f"🔍 GET /items - params: page={page}, category_id={category_id}, category_ids={category_ids}, status={status}")
        
        # Объединяем category_ids (поддержка обратной совместимости)
        if category_id:
            category_ids.append(str(category_id))
        
        # Преобразуем в integers и убираем дубликаты
        try:
            category_ids = list(set([int(cid) for cid in category_ids if cid and str(cid).isdigit()]))
        except (ValueError, TypeError) as e:
            print(f"❌ Ошибка преобразования category_ids: {e}")
            category_ids = []
        
        print(f"📂 Категории для фильтрации: {category_ids}")
        
        # Начинаем с базового запроса
        query = WarehouseItem.query
        
        # Фильтр по статусу
        if status and status != 'all':
            query = query.filter(WarehouseItem.status == status)
            print(f"🔖 Фильтр по статусу: {status}")
        
        # Фильтр по категориям через many-to-many связь
        if category_ids:
            try:
                # Получаем все дочерние категории для каждой выбранной категории
                all_category_ids = []
                for cat_id in category_ids:
                    all_category_ids.append(cat_id)
                    # Получаем категорию и её дочерние элементы
                    category = WarehouseCategory.query.get(cat_id)
                    if category:
                        child_ids = category.get_all_child_ids()
                        all_category_ids.extend(child_ids)
                        print(f"📁 Категория {cat_id} ({category.name}): +{len(child_ids)} дочерних")
                
                # Убираем дубликаты
                all_category_ids = list(set(all_category_ids))
                print(f"📋 Все категории для поиска: {all_category_ids}")
                
                # Используем связь many-to-many
                query = query.join(WarehouseItemCategory).filter(
                    WarehouseItemCategory.category_id.in_(all_category_ids)
                ).distinct()
                
            except Exception as e:
                print(f"❌ Ошибка фильтрации по категориям: {e}")
                # Продолжаем без фильтра по категориям
                pass
        
        # Поиск по тексту
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    WarehouseItem.name.ilike(search_filter),
                    WarehouseItem.barcode.ilike(search_filter),
                    WarehouseItem.sku.ilike(search_filter),
                    WarehouseItem.description.ilike(search_filter)
                )
            )
            print(f"🔎 Поиск по тексту: '{search}'")
        
        # Фильтр по остаткам
        if stock_filter and stock_filter != 'all':
            if stock_filter == 'low':
                query = query.filter(WarehouseItem.current_quantity <= WarehouseItem.min_quantity)
            elif stock_filter == 'out':
                query = query.filter(WarehouseItem.current_quantity == 0)
            elif stock_filter == 'overstocked':
                query = query.filter(WarehouseItem.current_quantity > WarehouseItem.max_quantity)
            elif stock_filter == 'normal':
                query = query.filter(
                    and_(
                        WarehouseItem.current_quantity > WarehouseItem.min_quantity,
                        WarehouseItem.current_quantity <= WarehouseItem.max_quantity
                    )
                )
            print(f"📊 Фильтр по остаткам: {stock_filter}")
        
        # Сортировка
        try:
            if sort_by == 'quantity':
                sort_column = WarehouseItem.current_quantity
            elif sort_by == 'value':
                sort_column = WarehouseItem.current_quantity * WarehouseItem.cost_price
            elif hasattr(WarehouseItem, sort_by):
                sort_column = getattr(WarehouseItem, sort_by)
            else:
                sort_column = WarehouseItem.name
            
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
                
        except Exception as e:
            print(f"❌ Ошибка сортировки: {e}")
            # По умолчанию сортируем по имени
            query = query.order_by(WarehouseItem.name.asc())
        
        # Подсчитываем общее количество перед пагинацией
        try:
            total_count = query.count()
            print(f"📈 Найдено товаров: {total_count}")
        except Exception as e:
            print(f"❌ Ошибка подсчета товаров: {e}")
            total_count = 0
        
        # Пагинация
        try:
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
        except Exception as e:
            print(f"❌ Ошибка пагинации: {e}")
            return jsonify({'error': f'Ошибка пагинации: {str(e)}'}), 500
        
        # Преобразуем товары в словари
        items_data = []
        for item in pagination.items:
            try:
                item_dict = item.to_dict(include_categories=True)
                items_data.append(item_dict)
            except Exception as e:
                print(f"❌ Ошибка преобразования товара {item.id}: {e}")
                # Добавляем базовую информацию
                items_data.append({
                    'id': item.id,
                    'name': item.name or 'Без названия',
                    'current_quantity': item.current_quantity or 0,
                    'unit': item.unit or 'шт',
                    'status': item.status or 'active',
                    'categories': [],
                    'category_names': []
                })
        
        result = {
            'items': items_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        print(f"✅ Возвращаем {len(items_data)} товаров")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Критическая ошибка в get_items: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': f'Ошибка получения товаров: {str(e)}',
            'items': [],
            'pagination': {
                'page': 1,
                'pages': 1,
                'per_page': per_page,
                'total': 0,
                'has_next': False,
                'has_prev': False
            }
        }), 500


@warehouse_bp.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    """Получить информацию о товаре"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        
        # Получаем последние операции с товаром
        recent_operations = WarehouseOperation.query.filter(
            WarehouseOperation.item_id == item_id
        ).order_by(desc(WarehouseOperation.created_at)).limit(10).all()
        
        return jsonify({
            'item': item.to_dict(),
            'recent_operations': [op.to_dict() for op in recent_operations]
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения товара: {str(e)}'}), 500


@warehouse_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    """Обновить товар с поддержкой множественных категорий"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        data = request.get_json()
        
        # Проверяем уникальность штрих-кода
        if data.get('barcode') and data['barcode'] != item.barcode:
            existing_item = WarehouseItem.query.filter(
                WarehouseItem.barcode == data['barcode'],
                WarehouseItem.id != item_id
            ).first()
            if existing_item:
                return jsonify({'error': 'Товар с таким штрих-кодом уже существует'}), 400
        
        # Проверяем уникальность SKU
        if data.get('sku') and data['sku'] != item.sku:
            existing_item = WarehouseItem.query.filter(
                WarehouseItem.sku == data['sku'],
                WarehouseItem.id != item_id
            ).first()
            if existing_item:
                return jsonify({'error': 'Товар с таким артикулом уже существует'}), 400
        
        # Обновляем поля товара (исключаем category_id - он больше не используется)
        for field in ['name', 'barcode', 'sku', 'description', 'unit', 
                     'min_quantity', 'max_quantity', 'cost_price', 'status']:
            if field in data:
                setattr(item, field, data[field])
        
        # Обработка категорий
        if any(key in data for key in ['category_ids', 'selectedCategories', 'category_names']):
            category_ids = []
            
            if data.get('category_ids'):
                category_ids.extend(data['category_ids'])
            
            if data.get('selectedCategories'):
                for category_name in data['selectedCategories']:
                    if category_name and category_name.strip():
                        category = WarehouseCategory.find_or_create_by_name(
                            name=category_name.strip()
                        )
                        category_ids.append(category.id)
            
            if data.get('category_names'):
                for category_name in data['category_names']:
                    if category_name and category_name.strip():
                        category = WarehouseCategory.find_or_create_by_name(
                            name=category_name.strip()
                        )
                        category_ids.append(category.id)
            
            # Убираем дубликаты и обновляем категории
            category_ids = list(set(category_ids))
            if category_ids:
                item.set_categories(category_ids)
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Товар обновлен успешно',
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка обновления товара: {str(e)}'}), 500


@warehouse_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    """Удалить товар"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        
        # Проверяем, есть ли остатки
        if item.current_quantity > 0:
            return jsonify({'error': 'Нельзя удалить товар с остатками на складе'}), 400
        
        # Помечаем как неактивный вместо физического удаления
        item.status = 'deleted'
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Товар удален успешно'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка удаления товара: {str(e)}'}), 500


@warehouse_bp.route('/items/search', methods=['GET'])
@jwt_required()
def search_items():
    """Поиск товаров для автодополнения с поддержкой множественных категорий"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 10, type=int), 50)
        category_ids = request.args.getlist('category_ids')
        category_id = request.args.get('category_id', type=int)
        
        if not query:
            return jsonify({'items': []})
        
        # Объединяем category_ids
        if category_id:
            category_ids.append(str(category_id))
        
        # Преобразуем в integers
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            category_ids = []
        
        from sqlalchemy import func

        search_filter = f"%{query}%"
        search_query = WarehouseItem.query.filter(
            WarehouseItem.status == 'active'
        ).filter(
            or_(
                func.lower(WarehouseItem.name).like(func.lower(search_filter)),
                func.lower(WarehouseItem.barcode).like(func.lower(search_filter)),
                func.lower(WarehouseItem.sku).like(func.lower(search_filter)),
                func.lower(WarehouseItem.description).like(func.lower(search_filter))
            )
        )
        
        # Фильтр по категориям
        if category_ids:
            categories = WarehouseCategory.query.filter(WarehouseCategory.id.in_(category_ids)).all()
            all_category_ids = set()
            for category in categories:
                all_category_ids.add(category.id)
                all_category_ids.update(category.get_all_child_ids())

        
        items = search_query.limit(limit).all()
        
        result_items = []
        for item in items:
            try:
                # Получаем категории товара
                categories = item.get_categories()
                category_names = [cat.name for cat in categories] if categories else []
                
                result_items.append({
                    'id': item.id,
                    'name': item.name,
                    'barcode': item.barcode,
                    'sku': item.sku,
                    'current_quantity': item.current_quantity,
                    'available_quantity': item.current_quantity - (item.reserved_quantity or 0),
                    'unit': item.unit,
                    'category_names': category_names
                })
            except Exception as e:
                print(f"❌ Ошибка обработки товара {item.id} в поиске: {e}")
                continue
        
        return jsonify({'items': result_items})
        
    except Exception as e:
        print(f"❌ Ошибка поиска товаров: {e}")
        return jsonify({'error': f'Ошибка поиска товаров: {str(e)}'}), 500


# ============ ОСТАТКИ ============

@warehouse_bp.route('/stock', methods=['GET'])
@jwt_required()
def get_stock():
    """Получить остатки товаров с поддержкой множественных категорий"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        
        # Поддержка множественных категорий
        category_ids = request.args.getlist('category_ids')
        category_id = request.args.get('category_id', type=int)
        
        search = request.args.get('search', '').strip()
        stock_filter = request.args.get('stock_filter')  # low, out, normal, overstocked, all
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        
        print(f"📦 GET /stock - params: category_ids={category_ids}, category_id={category_id}")
        
        # Объединяем category_ids
        if category_id:
            category_ids.append(str(category_id))
        
        # Преобразуем в integers
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            category_ids = []
        
        query = WarehouseItem.query.filter(WarehouseItem.status == 'active')
        
        # Фильтр по категориям через many-to-many связь
        if category_ids:
            # Получаем все дочерние категории
            all_category_ids = []
            for cat_id in category_ids:
                all_category_ids.append(cat_id)
                category = WarehouseCategory.query.get(cat_id)
                if category:
                    all_category_ids.extend(category.get_all_child_ids())
            
            all_category_ids = list(set(all_category_ids))
            query = query.join(WarehouseItemCategory).filter(
                WarehouseItemCategory.category_id.in_(all_category_ids)
            ).distinct()
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    WarehouseItem.name.ilike(search_filter),
                    WarehouseItem.barcode.ilike(search_filter),
                    WarehouseItem.sku.ilike(search_filter)
                )
            )
        
        # Фильтр по остаткам
        if stock_filter == 'low':
            query = query.filter(
                and_(
                    WarehouseItem.current_quantity > 0,
                    WarehouseItem.current_quantity <= WarehouseItem.min_quantity
                )
            )
        elif stock_filter == 'out':
            query = query.filter(WarehouseItem.current_quantity == 0)
        elif stock_filter == 'overstocked':
            query = query.filter(WarehouseItem.current_quantity > WarehouseItem.max_quantity)
        elif stock_filter == 'normal':
            query = query.filter(
                and_(
                    WarehouseItem.current_quantity > WarehouseItem.min_quantity,
                    WarehouseItem.current_quantity <= WarehouseItem.max_quantity
                )
            )
        
        # Сортировка
        if sort_by == 'quantity':
            sort_column = WarehouseItem.current_quantity
        elif sort_by == 'value':
            sort_column = WarehouseItem.current_quantity * WarehouseItem.cost_price
        elif hasattr(WarehouseItem, sort_by):
            sort_column = getattr(WarehouseItem, sort_by)
        else:
            sort_column = WarehouseItem.name
        
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
        
        # Добавляем расчетные поля
        items_data = []
        for item in pagination.items:
            try:
                item_dict = item.to_dict(include_categories=True)
                item_dict['total_value'] = item.current_quantity * (item.cost_price or 0)
                items_data.append(item_dict)
            except Exception as e:
                print(f"❌ Ошибка обработки товара {item.id} в остатках: {e}")
                # Базовая информация
                items_data.append({
                    'id': item.id,
                    'name': item.name or 'Без названия',
                    'current_quantity': item.current_quantity or 0,
                    'unit': item.unit or 'шт',
                    'cost_price': item.cost_price or 0,
                    'total_value': (item.current_quantity or 0) * (item.cost_price or 0),
                    'categories': [],
                    'category_names': []
                })
        
        # Статистика по текущей выборке
        total_items = pagination.total
        total_value = sum(item['total_value'] for item in items_data)
        
        return jsonify({
            'items': items_data,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'summary': {
                'total_items': total_items,
                'total_value': total_value
            }
        })
        
    except Exception as e:
        print(f"❌ Ошибка get_stock: {e}")
        return jsonify({'error': f'Ошибка получения остатков: {str(e)}'}), 500


# ============ ОПЕРАЦИИ ============

@warehouse_bp.route('/operations', methods=['GET'])
@jwt_required()
def get_operations():
    """Получить список операций с поддержкой фильтрации по категориям"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        item_id = request.args.get('item_id', type=int)
        operation_type = request.args.get('operation_type')
        user_id = request.args.get('user_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        
        # Поддержка фильтрации по категориям
        category_ids = request.args.getlist('category_ids')
        category_id = request.args.get('category_id', type=int)
        
        if category_id:
            category_ids.append(str(category_id))
        
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            category_ids = []
        
        query = WarehouseOperation.query
        
        # Фильтры
        if item_id:
            query = query.filter(WarehouseOperation.item_id == item_id)
        
        if operation_type:
            query = query.filter(WarehouseOperation.operation_type == operation_type)
        
        if user_id:
            query = query.filter(WarehouseOperation.user_id == user_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(WarehouseOperation.created_at >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Неверный формат даты date_from'}), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(WarehouseOperation.created_at < date_to_obj)
            except ValueError:
                return jsonify({'error': 'Неверный формат даты date_to'}), 400
        
        # Фильтр по категориям товаров
        if category_ids:
            # Получаем все дочерние категории
            all_category_ids = []
            for cat_id in category_ids:
                all_category_ids.append(cat_id)
                category = WarehouseCategory.query.get(cat_id)
                if category:
                    all_category_ids.extend(category.get_all_child_ids())
            
            all_category_ids = list(set(all_category_ids))
            
            # Фильтруем операции по товарам из выбранных категорий
            item_ids_in_categories = db.session.query(WarehouseItemCategory.item_id).filter(
                WarehouseItemCategory.category_id.in_(all_category_ids)
            ).distinct().subquery()
            
            query = query.filter(WarehouseOperation.item_id.in_(item_ids_in_categories))
        
        if search:
            search_filter = f"%{search}%"
            query = query.join(WarehouseItem).filter(
                or_(
                    WarehouseItem.name.ilike(search_filter),
                    WarehouseItem.barcode.ilike(search_filter),
                    WarehouseOperation.reason.ilike(search_filter),
                    WarehouseOperation.comment.ilike(search_filter)
                )
            )
        
        # Сортировка по дате (новые первые)
        query = query.order_by(desc(WarehouseOperation.created_at))
        
        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'operations': [op.to_dict() for op in pagination.items],
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения операций: {str(e)}'}), 500


@warehouse_bp.route('/operations/add-stock', methods=['POST'])
@jwt_required()
def add_stock():
    """Поступление товара на склад"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        # Валидация
        if not data.get('item_id') or not data.get('quantity'):
            return jsonify({'error': 'Товар и количество обязательны'}), 400
        
        quantity = int(data['quantity'])
        if quantity <= 0:
            return jsonify({'error': 'Количество должно быть положительным'}), 400
        
        item = WarehouseItem.query.get_or_404(data['item_id'])
        
        # Обновляем количество
        old_quantity = item.current_quantity
        new_quantity = old_quantity + quantity
        
        operation = item.update_quantity(
            new_quantity=new_quantity,
            operation_type='add',
            reason=data.get('reason', 'Поступление'),
            user_id=current_user_id
        )
        
        operation.comment = data.get('comment', '')
        operation.document_number = data.get('document_number', '')
        operation.ip_address = get_client_ip(request)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Добавлено {quantity} {item.unit} товара "{item.name}"',
            'operation': operation.to_dict(),
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка добавления товара: {str(e)}'}), 500


@warehouse_bp.route('/operations/remove-stock', methods=['POST'])
@jwt_required()
def remove_stock():
    """Списание товара со склада"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        # Валидация
        if not data.get('item_id') or not data.get('quantity'):
            return jsonify({'error': 'Товар и количество обязательны'}), 400
        
        quantity = int(data['quantity'])
        if quantity <= 0:
            return jsonify({'error': 'Количество должно быть положительным'}), 400
        
        item = WarehouseItem.query.get_or_404(data['item_id'])
        
        # Проверяем достаточность остатков
        available_quantity = item.current_quantity - (item.reserved_quantity or 0)
        if quantity > available_quantity:
            return jsonify({
                'error': f'Недостаточно товара на складе. Доступно: {available_quantity} {item.unit}'
            }), 400
        
        # Обновляем количество
        old_quantity = item.current_quantity
        new_quantity = old_quantity - quantity
        
        operation = item.update_quantity(
            new_quantity=new_quantity,
            operation_type='remove',
            reason=data.get('reason', 'Списание'),
            user_id=current_user_id
        )
        
        operation.comment = data.get('comment', '')
        operation.document_number = data.get('document_number', '')
        operation.ip_address = get_client_ip(request)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Списано {quantity} {item.unit} товара "{item.name}"',
            'operation': operation.to_dict(),
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка списания товара: {str(e)}'}), 500


# ============ УТИЛИТЫ И УПРАВЛЕНИЕ КАТЕГОРИЯМИ ТОВАРОВ ============

@warehouse_bp.route('/items/<int:item_id>/categories', methods=['GET'])
@jwt_required()
def get_item_categories(item_id):
    """Получить категории товара"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        categories = item.get_categories()
        
        return jsonify({
            'item_id': item_id,
            'categories': [cat.to_dict() for cat in categories]
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения категорий товара: {str(e)}'}), 500


@warehouse_bp.route('/items/<int:item_id>/categories', methods=['POST'])
@jwt_required()
def add_item_categories(item_id):
    """Добавить категории к товару"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        data = request.get_json()
        
        category_ids = data.get('category_ids', [])
        if not category_ids:
            return jsonify({'error': 'Не указаны категории'}), 400
        
        # Добавляем категории
        for category_id in category_ids:
            item.add_category(category_id)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Добавлены категории к товару "{item.name}"',
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка добавления категорий: {str(e)}'}), 500


@warehouse_bp.route('/items/<int:item_id>/categories', methods=['PUT'])
@jwt_required()
def set_item_categories(item_id):
    """Установить категории товара (заменить все существующие)"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        data = request.get_json()
        
        category_ids = data.get('category_ids', [])
        
        # Устанавливаем категории (заменяем все существующие)
        item.set_categories(category_ids)
        db.session.commit()
        
        return jsonify({
            'message': f'Обновлены категории товара "{item.name}"',
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка обновления категорий: {str(e)}'}), 500


@warehouse_bp.route('/items/<int:item_id>/categories', methods=['DELETE'])
@jwt_required()
def remove_item_categories(item_id):
    """Удалить категории у товара"""
    try:
        item = WarehouseItem.query.get_or_404(item_id)
        data = request.get_json()
        
        category_ids = data.get('category_ids', [])
        if not category_ids:
            return jsonify({'error': 'Не указаны категории для удаления'}), 400
        
        # Удаляем категории
        for category_id in category_ids:
            item.remove_category(category_id)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Удалены категории у товара "{item.name}"',
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка удаления категорий: {str(e)}'}), 500


# ============ КОНСТАНТЫ И УТИЛИТЫ ============

@warehouse_bp.route('/barcode/info', methods=['POST'])
@jwt_required()
def get_barcode_info():
    """Получить информацию о товаре по штрих-коду"""
    try:
        data = request.get_json()
        barcode = data.get('barcode', '').strip()
        
        if not barcode:
            return jsonify({'error': 'Штрих-код обязателен'}), 400
        
        # Сначала проверяем наличие в нашей базе
        existing_item = WarehouseItem.query.filter(
            WarehouseItem.barcode == barcode
        ).first()
        
        if existing_item:
            return jsonify({
                'success' : True,
                'found_in_database': True,
                'item': existing_item.to_dict(),
                'message': 'Товар найден в базе данных'
            })
        
        # Получаем данные из внешнего сервиса
        product_data = get_product_from_service_online(barcode)
        if not product_data:
            return jsonify({
                'success' : False,
                'found_in_database': False,
                'barcode': barcode,
                'message': 'Информация не найдена во внешнем источнике'
            }), 404
        
        import time
        time.sleep(0.5)
        
        return jsonify({
            'success' : True,
            'found_in_database': False,
            'external_data': product_data,
            'barcode': barcode,
            'message': 'Информация получена из внешнего источника'
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения информации: {str(e)}'}), 500


@warehouse_bp.route('/constants', methods=['GET'])
@jwt_required()
def get_constants():
    """Получить константы для UI"""
    try:
        from models import OPERATION_TYPES, REMOVAL_REASONS, ADDITION_REASONS
        
        return jsonify({
            'operation_types': OPERATION_TYPES,
            'removal_reasons': REMOVAL_REASONS,
            'addition_reasons': ADDITION_REASONS,
            'stock_filters': {
                'all': 'Все товары',
                'normal': 'Нормальные остатки',
                'low': 'Низкие остатки',
                'out': 'Нет в наличии',
                'overstocked': 'Избыток'
            },
            'item_statuses': {
                'active': 'Активный',
                'inactive': 'Неактивный',
                'discontinued': 'Снят с производства'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения констант: {str(e)}'}), 500


# ============ ЭКСПОРТ ДАННЫХ ============

@warehouse_bp.route('/export/stock', methods=['GET'])
@jwt_required()
def export_stock():
    """Экспорт остатков в CSV с поддержкой множественных категорий"""
    try:
        # Поддержка множественных категорий
        category_ids = request.args.getlist('category_ids')
        category_id = request.args.get('category_id', type=int)
        stock_filter = request.args.get('stock_filter')
        
        if category_id:
            category_ids.append(str(category_id))
        
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            category_ids = []
        
        query = WarehouseItem.query.filter(WarehouseItem.status == 'active')
        
        # Фильтр по категориям через many-to-many связь
        if category_ids:
            # Получаем все дочерние категории
            all_category_ids = []
            for cat_id in category_ids:
                all_category_ids.append(cat_id)
                category = WarehouseCategory.query.get(cat_id)
                if category:
                    all_category_ids.extend(category.get_all_child_ids())
            
            all_category_ids = list(set(all_category_ids))
            query = query.join(WarehouseItemCategory).filter(
                WarehouseItemCategory.category_id.in_(all_category_ids)
            ).distinct()
        
        # Фильтр по остаткам
        if stock_filter == 'low':
            query = query.filter(
                and_(
                    WarehouseItem.current_quantity > 0,
                    WarehouseItem.current_quantity <= WarehouseItem.min_quantity
                )
            )
        elif stock_filter == 'out':
            query = query.filter(WarehouseItem.current_quantity == 0)
        elif stock_filter == 'overstocked':
            query = query.filter(WarehouseItem.current_quantity > WarehouseItem.max_quantity)
        
        items = query.order_by(WarehouseItem.name).all()
        
        # Создаем CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'Название', 'Штрих-код', 'Артикул', 'Категории', 'Единица',
            'Текущее количество', 'Зарезервировано', 'Доступно',
            'Мин. количество', 'Макс. количество', 'Себестоимость',
            'Общая стоимость', 'Статус остатков', 'Последняя операция'
        ])
        
        # Данные
        for item in items:
            try:
                # Получаем категории товара
                categories = item.get_categories()
                category_names = [cat.name for cat in categories] if categories else ['Без категории']
                
                available_qty = item.current_quantity - (item.reserved_quantity or 0)
                total_value = item.current_quantity * (float(item.cost_price) if item.cost_price else 0)
                
                # Определяем статус остатков
                if item.current_quantity == 0:
                    stock_status = 'Нет в наличии'
                elif item.current_quantity <= item.min_quantity:
                    stock_status = 'Низкий остаток'
                elif item.current_quantity > item.max_quantity:
                    stock_status = 'Избыток'
                else:
                    stock_status = 'Нормально'
                
                writer.writerow([
                    item.name,
                    item.barcode or '',
                    item.sku or '',
                    ', '.join(category_names),  # Объединяем категории через запятую
                    item.unit,
                    item.current_quantity,
                    item.reserved_quantity or 0,
                    available_qty,
                    item.min_quantity,
                    item.max_quantity,
                    float(item.cost_price) if item.cost_price else 0,
                    total_value,
                    stock_status,
                    item.last_operation_at.strftime('%Y-%m-%d %H:%M:%S') if item.last_operation_at else ''
                ])
            except Exception as e:
                print(f"❌ Ошибка экспорта товара {item.id}: {e}")
                continue
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=warehouse_stock_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Ошибка экспорта остатков: {str(e)}'}), 500


# ============ ДИАГНОСТИКА И ОТЛАДКА ============

@warehouse_bp.route('/debug/status', methods=['GET'])
@jwt_required()
def warehouse_debug_status():
    """Диагностика состояния склада"""
    try:
        status = {
            'database_connection': True,
            'tables_exist': {},
            'data_counts': {},
            'issues': [],
            'suggestions': []
        }
        
        # Проверяем существование таблиц и данных
        tables_to_check = [
            ('warehouse_categories', WarehouseCategory),
            ('warehouse_items', WarehouseItem), 
            ('warehouse_item_categories', WarehouseItemCategory),
            ('warehouse_operations', WarehouseOperation)
        ]
        
        for table_name, model_class in tables_to_check:
            try:
                count = model_class.query.count()
                status['tables_exist'][table_name] = True
                status['data_counts'][table_name] = count
            except Exception as e:
                status['tables_exist'][table_name] = False
                status['issues'].append(f"Таблица {table_name} недоступна: {e}")
        
        # Проверяем целостность данных
        try:
            # Товары без категорий
            items_without_categories = db.session.query(WarehouseItem).filter(
                ~WarehouseItem.id.in_(
                    db.session.query(WarehouseItemCategory.item_id)
                )
            ).count()
            
            if items_without_categories > 0:
                status['issues'].append(f"Найдено {items_without_categories} товаров без категорий")
                status['suggestions'].append("Выполните: flask migrate-warehouse")
            
            # Некорректные связи
            orphaned_relations = db.session.query(WarehouseItemCategory).filter(
                ~WarehouseItemCategory.item_id.in_(
                    db.session.query(WarehouseItem.id)
                ) | ~WarehouseItemCategory.category_id.in_(
                    db.session.query(WarehouseCategory.id)
                )
            ).count()
            
            if orphaned_relations > 0:
                status['issues'].append(f"Найдено {orphaned_relations} некорректных связей товар-категория")
                status['suggestions'].append("Выполните: flask fix-warehouse")
                
        except Exception as e:
            status['issues'].append(f"Ошибка проверки целостности: {e}")
        
        # Общая оценка
        if len(status['issues']) == 0:
            status['overall_status'] = 'healthy'
            status['message'] = 'Склад работает корректно'
        elif len(status['issues']) <= 2:
            status['overall_status'] = 'warning'
            status['message'] = 'Найдены незначительные проблемы'
        else:
            status['overall_status'] = 'error'
            status['message'] = 'Обнаружены серьезные проблемы'
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'database_connection': False,
            'error': f'Критическая ошибка диагностики: {str(e)}',
            'overall_status': 'critical'
        }), 500


@warehouse_bp.route('/debug/fix', methods=['POST'])
@jwt_required()
def warehouse_debug_fix():
    """Автоматическое исправление проблем склада"""
    try:
        results = {
            'fixed_issues': [],
            'remaining_issues': [],
            'actions_taken': []
        }
        
        # 1. Создаем отсутствующие таблицы
        try:
            db.create_all()
            results['actions_taken'].append('Проверены/созданы все таблицы')
        except Exception as e:
            results['remaining_issues'].append(f'Ошибка создания таблиц: {e}')
        
        # 2. Исправляем товары без категорий
        try:
            from models import migrate_existing_items_to_multiple_categories
            migrate_existing_items_to_multiple_categories()
            results['actions_taken'].append('Добавлены категории для товаров без категорий')
        except Exception as e:
            results['remaining_issues'].append(f'Ошибка миграции товаров: {e}')
        
        # 3. Удаляем некорректные связи
        try:
            orphaned_relations = db.session.query(WarehouseItemCategory).filter(
                ~WarehouseItemCategory.item_id.in_(
                    db.session.query(WarehouseItem.id)
                ) | ~WarehouseItemCategory.category_id.in_(
                    db.session.query(WarehouseCategory.id)
                )
            ).all()
            
            for relation in orphaned_relations:
                db.session.delete(relation)
            
            if orphaned_relations:
                db.session.commit()
                results['fixed_issues'].append(f'Удалено {len(orphaned_relations)} некорректных связей')
                results['actions_taken'].append('Очищены некорректные связи товар-категория')
            
        except Exception as e:
            results['remaining_issues'].append(f'Ошибка очистки связей: {e}')
        
        # 4. Создаем примеры данных если их нет
        try:
            if WarehouseCategory.query.count() == 0:
                from models import create_sample_warehouse_data
                create_sample_warehouse_data()
                results['actions_taken'].append('Созданы примеры данных склада')
        except Exception as e:
            results['remaining_issues'].append(f'Ошибка создания примеров данных: {e}')
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': f'Критическая ошибка исправления: {str(e)}',
            'fixed_issues': [],
            'remaining_issues': [str(e)]
        }), 500


# ============ АНАЛИТИКА ============

@warehouse_bp.route('/analytics/stock-movement', methods=['GET'])
@jwt_required()
def get_stock_movement_analytics():
    """Аналитика движения товаров с поддержкой фильтрации по категориям"""
    try:
        days = request.args.get('days', 30, type=int)
        category_ids = request.args.getlist('category_ids')
        category_id = request.args.get('category_id', type=int)
        
        if category_id:
            category_ids.append(str(category_id))
        
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            category_ids = []
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = WarehouseOperation.query.filter(
            WarehouseOperation.created_at >= start_date
        )
        
        # Фильтр по категориям товаров
        if category_ids:
            # Получаем все дочерние категории
            all_category_ids = []
            for cat_id in category_ids:
                all_category_ids.append(cat_id)
                category = WarehouseCategory.query.get(cat_id)
                if category:
                    all_category_ids.extend(category.get_all_child_ids())
            
            all_category_ids = list(set(all_category_ids))
            
            # Фильтруем операции по товарам из выбранных категорий
            item_ids_in_categories = db.session.query(WarehouseItemCategory.item_id).filter(
                WarehouseItemCategory.category_id.in_(all_category_ids)
            ).distinct().subquery()
            
            query = query.filter(WarehouseOperation.item_id.in_(item_ids_in_categories))
        
        # Группировка по дням
        daily_stats = db.session.query(
            func.date(WarehouseOperation.created_at).label('date'),
            WarehouseOperation.operation_type,
            func.count(WarehouseOperation.id).label('count'),
            func.sum(func.abs(WarehouseOperation.quantity_change)).label('quantity')
        ).filter(
            WarehouseOperation.created_at >= start_date
        )
        
        # Применяем фильтр по категориям к группировке
        if category_ids:
            daily_stats = daily_stats.filter(WarehouseOperation.item_id.in_(item_ids_in_categories))
        
        daily_stats = daily_stats.group_by(
            func.date(WarehouseOperation.created_at),
            WarehouseOperation.operation_type
        ).all()
        
        # Форматируем данные для графиков
        chart_data = {}
        for stat in daily_stats:
            date_str = stat.date.isoformat()
            if date_str not in chart_data:
                chart_data[date_str] = {}
            chart_data[date_str][stat.operation_type] = {
                'count': stat.count,
                'quantity': int(stat.quantity) if stat.quantity else 0
            }
        
        # Топ товаров по активности в выбранных категориях
        top_items_query = db.session.query(
            WarehouseItem.id,
            WarehouseItem.name,
            func.count(WarehouseOperation.id).label('operation_count'),
            func.sum(func.abs(WarehouseOperation.quantity_change)).label('total_quantity')
        ).join(WarehouseOperation).filter(
            WarehouseOperation.created_at >= start_date
        )
        
        if category_ids:
            top_items_query = top_items_query.filter(WarehouseItem.id.in_(item_ids_in_categories))
        
        top_items = top_items_query.group_by(WarehouseItem.id).order_by(
            desc(func.count(WarehouseOperation.id))
        ).limit(10).all()
        
        return jsonify({
            'period_days': days,
            'category_filter': category_ids,
            'daily_movement': chart_data,
            'top_active_items': [
                {
                    'id': item_id,
                    'name': name,
                    'operation_count': count,
                    'total_quantity': int(quantity) if quantity else 0
                }
                for item_id, name, count, quantity in top_items
            ]
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка аналитики: {str(e)}'}), 500


@warehouse_bp.route('/analytics/low-stock-alerts', methods=['GET'])
@jwt_required()
def get_low_stock_alerts():
    """Уведомления о низких остатках с поддержкой фильтрации по категориям"""
    try:
        category_ids = request.args.getlist('category_ids')
        category_id = request.args.get('category_id', type=int)
        
        if category_id:
            category_ids.append(str(category_id))
        
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            category_ids = []
        
        # Базовые запросы
        base_filter = [WarehouseItem.status == 'active']
        
        # Если указаны категории, добавляем фильтр
        if category_ids:
            # Получаем все дочерние категории
            all_category_ids = []
            for cat_id in category_ids:
                all_category_ids.append(cat_id)
                category = WarehouseCategory.query.get(cat_id)
                if category:
                    all_category_ids.extend(category.get_all_child_ids())
            
            all_category_ids = list(set(all_category_ids))
            
            # Фильтр по категориям
            category_filter = WarehouseItem.id.in_(
                db.session.query(WarehouseItemCategory.item_id).filter(
                    WarehouseItemCategory.category_id.in_(all_category_ids)
                )
            )
            base_filter.append(category_filter)
        
        # Товары с низкими остатками
        low_stock_items = WarehouseItem.query.filter(
            and_(
                WarehouseItem.current_quantity <= WarehouseItem.min_quantity,
                WarehouseItem.current_quantity > 0,
                *base_filter
            )
        ).order_by(WarehouseItem.current_quantity.asc()).all()
        
        # Товары, которых нет в наличии
        out_of_stock_items = WarehouseItem.query.filter(
            and_(
                WarehouseItem.current_quantity == 0,
                *base_filter
            )
        ).order_by(WarehouseItem.last_operation_at.desc()).all()
        
        # Товары с избытком
        overstocked_items = WarehouseItem.query.filter(
            and_(
                WarehouseItem.current_quantity > WarehouseItem.max_quantity,
                *base_filter
            )
        ).order_by(WarehouseItem.current_quantity.desc()).all()
        
        return jsonify({
            'category_filter': category_ids,
            'low_stock': [item.to_dict() for item in low_stock_items],
            'out_of_stock': [item.to_dict() for item in out_of_stock_items],
            'overstocked': [item.to_dict() for item in overstocked_items],
            'summary': {
                'low_stock_count': len(low_stock_items),
                'out_of_stock_count': len(out_of_stock_items),
                'overstocked_count': len(overstocked_items)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения уведомлений: {str(e)}'}), 500


# ============ МАССОВЫЕ ОПЕРАЦИИ ============

@warehouse_bp.route('/operations/bulk-add', methods=['POST'])
@jwt_required()
def bulk_add_stock():
    """Массовое поступление товаров"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        items_data = data.get('items', [])
        if not items_data:
            return jsonify({'error': 'Список товаров не может быть пустым'}), 400
        
        operations = []
        updated_items = []
        errors = []
        
        for item_data in items_data:
            try:
                item_id = item_data.get('item_id')
                quantity = int(item_data.get('quantity', 0))
                
                if not item_id or quantity <= 0:
                    errors.append(f'Неверные данные для товара ID {item_id}')
                    continue
                
                item = WarehouseItem.query.get(item_id)
                if not item:
                    errors.append(f'Товар с ID {item_id} не найден')
                    continue
                
                old_quantity = item.current_quantity
                new_quantity = old_quantity + quantity
                
                operation = item.update_quantity(
                    new_quantity=new_quantity,
                    operation_type='add',
                    reason=item_data.get('reason', 'Массовое поступление'),
                    user_id=current_user_id
                )
                
                operation.comment = item_data.get('comment', '')
                operation.document_number = data.get('document_number', '')
                operation.ip_address = get_client_ip(request)
                
                operations.append(operation)
                updated_items.append(item)
                
            except Exception as e:
                errors.append(f'Ошибка обработки товара ID {item_data.get("item_id")}: {str(e)}')
        
        if operations:
            db.session.commit()
        
        return jsonify({
            'message': f'Обработано {len(operations)} товаров',
            'success_count': len(operations),
            'error_count': len(errors),
            'errors': errors,
            'operations': [op.to_dict() for op in operations]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка массового поступления: {str(e)}'}), 500


@warehouse_bp.route('/operations/bulk-remove', methods=['POST'])
@jwt_required()
def bulk_remove_stock():
    """Массовое списание товаров"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        items_data = data.get('items', [])
        if not items_data:
            return jsonify({'error': 'Список товаров не может быть пустым'}), 400
        
        operations = []
        updated_items = []
        errors = []
        
        for item_data in items_data:
            try:
                item_id = item_data.get('item_id')
                quantity = int(item_data.get('quantity', 0))
                
                if not item_id or quantity <= 0:
                    errors.append(f'Неверные данные для товара ID {item_id}')
                    continue
                
                item = WarehouseItem.query.get(item_id)
                if not item:
                    errors.append(f'Товар с ID {item_id} не найден')
                    continue
                
                available_quantity = item.current_quantity - (item.reserved_quantity or 0)
                if quantity > available_quantity:
                    errors.append(f'Товар "{item.name}": недостаточно остатков ({available_quantity} доступно)')
                    continue
                
                old_quantity = item.current_quantity
                new_quantity = old_quantity - quantity
                
                operation = item.update_quantity(
                    new_quantity=new_quantity,
                    operation_type='remove',
                    reason=item_data.get('reason', 'Массовое списание'),
                    user_id=current_user_id
                )
                
                operation.comment = item_data.get('comment', '')
                operation.document_number = data.get('document_number', '')
                operation.ip_address = get_client_ip(request)
                
                operations.append(operation)
                updated_items.append(item)
                
            except Exception as e:
                errors.append(f'Ошибка обработки товара ID {item_data.get("item_id")}: {str(e)}')
        
        if operations:
            db.session.commit()
        
        return jsonify({
            'message': f'Обработано {len(operations)} товаров',
            'success_count': len(operations),
            'error_count': len(errors),
            'errors': errors,
            'operations': [op.to_dict() for op in operations]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка массового списания: {str(e)}'}), 500


# ============ ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ ============

@warehouse_bp.route('/categories/hierarchy', methods=['GET'])
@jwt_required()
def get_category_hierarchy():
    """Получить полную иерархию категорий"""
    try:
        # Получаем все категории
        all_categories = WarehouseCategory.query.order_by(WarehouseCategory.name).all()
        
        # Строим иерархию
        def build_hierarchy(parent_id=None):
            children = []
            for category in all_categories:
                if category.parent_id == parent_id:
                    cat_data = category.to_dict()
                    cat_data['items_count'] = category.get_items_count(include_subcategories=True)
                    cat_data['children'] = build_hierarchy(category.id)
                    children.append(cat_data)
            return children
        
        hierarchy = build_hierarchy()
        
        return jsonify({
            'hierarchy': hierarchy,
            'total_categories': len(all_categories)
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения иерархии: {str(e)}'}), 500


@warehouse_bp.route('/categories/<int:category_id>/path', methods=['GET'])
@jwt_required()
def get_category_path(category_id):
    """Получить путь к категории (breadcrumbs)"""
    try:
        category = WarehouseCategory.query.get_or_404(category_id)
        
        # Строим путь от корня до текущей категории
        path = []
        current = category
        
        while current:
            path.insert(0, {
                'id': current.id,
                'name': current.name,
                'color': current.color
            })
            current = current.parent
        
        return jsonify({
            'category_id': category_id,
            'path': path,
            'full_path': category.get_full_path()
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения пути категории: {str(e)}'}), 500


@warehouse_bp.route('/items/by-categories', methods=['GET'])
@jwt_required()
def get_items_by_categories():
    """Получить товары из указанных категорий (включая подкатегории)"""
    try:
        category_ids = request.args.getlist('category_ids')
        include_subcategories = request.args.get('include_subcategories', 'true').lower() == 'true'
        status = request.args.get('status', 'active')
        
        if not category_ids:
            return jsonify({'error': 'Не указаны категории'}), 400
        
        try:
            category_ids = [int(cid) for cid in category_ids if cid and str(cid).isdigit()]
        except (ValueError, TypeError):
            return jsonify({'error': 'Неверный формат ID категорий'}), 400
        
        # Расширяем список категорий подкатегориями если нужно
        all_category_ids = category_ids.copy()
        
        if include_subcategories:
            for cat_id in category_ids:
                category = WarehouseCategory.query.get(cat_id)
                if category:
                    all_category_ids.extend(category.get_all_child_ids())
        
        all_category_ids = list(set(all_category_ids))
        
        # Получаем товары
        query = WarehouseItem.query.join(WarehouseItemCategory).filter(
            WarehouseItemCategory.category_id.in_(all_category_ids),
            WarehouseItem.status == status
        ).distinct()
        
        items = query.order_by(WarehouseItem.name).all()
        
        return jsonify({
            'category_ids': category_ids,
            'all_category_ids': all_category_ids,
            'include_subcategories': include_subcategories,
            'items': [item.to_dict() for item in items],
            'total_items': len(items)
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения товаров по категориям: {str(e)}'}), 500