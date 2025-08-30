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