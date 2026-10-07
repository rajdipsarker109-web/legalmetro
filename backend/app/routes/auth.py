import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.utils.helpers import new_id

auth_bp = Blueprint('auth', __name__)


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    required = ['name', 'email', 'password']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'Name, email and password are required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        id=new_id(),
        name=data['name'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        role='business_owner',
        phone=data.get('phone'),
        organisation=data.get('organisation'),
        state=data.get('state'),
        district=data.get('district'),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not check_password(data.get('password', ''), user.password_hash):
        return jsonify({'error': 'Invalid email or password'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    return jsonify({'token': token, 'user': user.to_dict()})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'})
