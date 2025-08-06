# routes/portfolio.py
from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from models import db, Portfolio

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/', methods=['GET'])
def get_portfolio():
    """Получить портфолио с фильтрацией"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 12, type=int), 100)
    category = request.args.get('category')
    featured = request.args.get('featured', type=bool)
    
    query = Portfolio.query
    
    if category and category != 'all':
        query = query.filter(Portfolio.category == category)
    
    if featured:
        query = query.filter(Portfolio.featured == True)
    
    query = query.order_by(desc(Portfolio.date))
    
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'portfolio': [item.to_dict() for item in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
def get_portfolio_item(portfolio_id):
    """Получить детали работы портфолио"""
    item = Portfolio.query.get_or_404(portfolio_id)
    
    # Связанные работы той же категории
    related_items = Portfolio.query.filter(
        Portfolio.category == item.category,
        Portfolio.id != item.id
    ).limit(4).all()
    
    return jsonify({
        'portfolio_item': item.to_dict(),
        'related_items': [item.to_dict() for item in related_items]
    })

@portfolio_bp.route('/categories', methods=['GET'])
def get_portfolio_categories():
    """Получить категории портфолио"""
    from sqlalchemy import func
    
    categories_data = db.session.query(
        Portfolio.category,
        func.count(Portfolio.id).label('count')
    ).group_by(Portfolio.category).all()
    
    categories = [
        {'id': 'all', 'name': 'Все работы', 'count': Portfolio.query.count()}
    ]
    
    category_names = {
        'children': 'Детские праздники',
        'wedding': 'Свадьбы',
        'corporate': 'Корпоративы',
        'anniversary': 'Юбилеи',
        'show': 'Шоу-программы'
    }
    
    for category, count in categories_data:
        categories.append({
            'id': category,
            'name': category_names.get(category, category.title()),
            'count': count
        })
    
    return jsonify({'categories': categories})

@portfolio_bp.route('/featured', methods=['GET'])
def get_featured_portfolio():
    """Получить избранные работы"""
    limit = request.args.get('limit', 6, type=int)
    
    items = Portfolio.query.filter(
        Portfolio.featured == True
    ).order_by(desc(Portfolio.date)).limit(limit).all()
    
    return jsonify({
        'portfolio': [item.to_dict() for item in items]
    })

# routes/team.py
from flask import Blueprint, request, jsonify
from models import db, TeamMember

team_bp = Blueprint('team', __name__)

@team_bp.route('/', methods=['GET'])
def get_team():
    """Получить список команды"""
    active_only = request.args.get('active_only', True, type=bool)
    
    query = TeamMember.query
    
    if active_only:
        query = query.filter(TeamMember.active == True)
    
    team_members = query.all()
    
    return jsonify({
        'team_members': [member.to_dict() for member in team_members]
    })

@team_bp.route('/<int:member_id>', methods=['GET'])
def get_team_member(member_id):
    """Получить информацию о сотруднике"""
    member = TeamMember.query.get_or_404(member_id)
    return jsonify({'team_member': member.to_dict()})

@team_bp.route('/animators', methods=['GET'])
def get_animators():
    """Получить только аниматоров"""
    animators = TeamMember.query.filter(
        TeamMember.role.contains('Аниматор'),
        TeamMember.active == True
    ).all()
    
    return jsonify({
        'animators': [member.to_dict() for member in animators]
    })

@team_bp.route('/hosts', methods=['GET'])
def get_hosts():
    """Получить только ведущих"""
    hosts = TeamMember.query.filter(
        TeamMember.role.contains('Ведущ'),
        TeamMember.active == True
    ).all()
    
    return jsonify({
        'hosts': [member.to_dict() for member in hosts]
    })

# routes/analytics.py
