from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.notification import Notification
from app.models.user import User

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications/', methods=['GET'])
@jwt_required()
def list_notifications():
    user = User.query.get(get_jwt_identity())
    notes = Notification.query.filter_by(user_id=user.id).order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    return jsonify([n.to_dict() for n in notes])


@notifications_bp.route('/notifications/<note_id>/read', methods=['PATCH'])
@jwt_required()
def mark_read(note_id):
    user = User.query.get(get_jwt_identity())
    note = Notification.query.get(note_id)
    if not note or note.user_id != user.id:
        return jsonify({'error': 'Not found'}), 404
    note.is_read = True
    db.session.commit()
    return jsonify(note.to_dict())
