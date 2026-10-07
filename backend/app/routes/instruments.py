import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.instrument import Instrument
from app.models.certificate import Certificate
from app.models.audit_log import AuditLog
from app.utils.helpers import new_id, generate_instrument_id
from app.utils.decorators import role_required
from app.services.qr_service import generate_qr
from app.services.hash_service import create_audit_log
from datetime import date

instruments_bp = Blueprint('instruments', __name__)


@instruments_bp.route('/instruments/', methods=['POST'])
@role_required('business_owner')
def register_instrument(current_user):
    data = request.form
    required = ['instrument_type', 'usage_state', 'usage_district']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'instrument_type, usage_state, usage_district required'}), 400

    upload_folder = current_app.config['UPLOAD_FOLDER']
    docs_dir = os.path.join(upload_folder, 'docs')
    os.makedirs(docs_dir, exist_ok=True)

    model_cert_url = None
    invoice_url = None
    if 'model_approval_certificate' in request.files:
        f = request.files['model_approval_certificate']
        if f.filename:
            fn = secure_filename(f"mac_{new_id()[:8]}_{f.filename}")
            f.save(os.path.join(docs_dir, fn))
            model_cert_url = f"/uploads/docs/{fn}"
    if 'purchase_invoice' in request.files:
        f = request.files['purchase_invoice']
        if f.filename:
            fn = secure_filename(f"inv_{new_id()[:8]}_{f.filename}")
            f.save(os.path.join(docs_dir, fn))
            invoice_url = f"/uploads/docs/{fn}"

    uid = generate_instrument_id(data.get('usage_state'))
    qr_url = generate_qr(uid, current_app.config['FRONTEND_URL'], upload_folder)

    instrument = Instrument(
        id=new_id(),
        unique_instrument_id=uid,
        owner_id=current_user.id,
        instrument_type=data.get('instrument_type'),
        make=data.get('make'),
        model_name=data.get('model_name'),
        serial_number=data.get('serial_number'),
        manufacturer_name=data.get('manufacturer_name'),
        usage_state=data.get('usage_state'),
        usage_district=data.get('usage_district'),
        usage_address=data.get('usage_address'),
        model_approval_cert_url=model_cert_url,
        purchase_invoice_url=invoice_url,
        qr_code_url=qr_url,
        current_status='registered',
    )
    db.session.add(instrument)
    create_audit_log(instrument.id, 'registered', current_user.id,
                     f'Instrument {uid} registered')
    db.session.commit()
    return jsonify(instrument.to_dict()), 201


@instruments_bp.route('/instruments/', methods=['GET'])
@jwt_required()
def list_instruments():
    user = User.query.get(get_jwt_identity())
    q = Instrument.query
    if user.role == 'business_owner':
        q = q.filter_by(owner_id=user.id)
    elif user.role == 'super_admin':
        if request.args.get('state'):
            q = q.filter_by(usage_state=request.args.get('state'))
        if request.args.get('district'):
            q = q.filter_by(usage_district=request.args.get('district'))
        if request.args.get('status'):
            q = q.filter_by(current_status=request.args.get('status'))
        if request.args.get('q'):
            term = f"%{request.args.get('q')}%"
            q = q.filter(
                db.or_(
                    Instrument.unique_instrument_id.like(term),
                    Instrument.serial_number.like(term),
                )
            )
    else:
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify([i.to_dict() for i in q.order_by(Instrument.created_at.desc()).all()])


@instruments_bp.route('/instruments/<instrument_id>', methods=['GET'])
@jwt_required()
def get_instrument(instrument_id):
    user = User.query.get(get_jwt_identity())
    inst = Instrument.query.get(instrument_id)
    if not inst:
        return jsonify({'error': 'Not found'}), 404
    if user.role == 'business_owner' and inst.owner_id != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify(inst.to_dict())


@instruments_bp.route('/instruments/<instrument_id>/history', methods=['GET'])
@jwt_required()
def instrument_history(instrument_id):
    user = User.query.get(get_jwt_identity())
    inst = Instrument.query.get(instrument_id)
    if not inst:
        return jsonify({'error': 'Not found'}), 404
    if user.role == 'business_owner' and inst.owner_id != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    logs = AuditLog.query.filter_by(instrument_id=instrument_id).order_by(AuditLog.timestamp).all()
    return jsonify([l.to_dict() for l in logs])


@instruments_bp.route('/instruments/<instrument_id>/certs', methods=['GET'])
@jwt_required()
def instrument_certs(instrument_id):
    user = User.query.get(get_jwt_identity())
    inst = Instrument.query.get(instrument_id)
    if not inst:
        return jsonify({'error': 'Not found'}), 404
    if user.role == 'business_owner' and inst.owner_id != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    certs = Certificate.query.filter_by(instrument_id=instrument_id).order_by(
        Certificate.issue_date.desc()
    ).all()
    return jsonify([c.to_dict() for c in certs])


@instruments_bp.route('/verify/<unique_id>', methods=['GET'])
def public_verify(unique_id):
    inst = Instrument.query.filter_by(unique_instrument_id=unique_id).first()
    if not inst:
        return jsonify({'error': 'not_found', 'message': 'Instrument not found'}), 404

    today = date.today()
    display_status = inst.current_status
    days_left = None
    if inst.cert_valid_until:
        days_left = (inst.cert_valid_until - today).days
        if inst.current_status == 'verified' and days_left < 0:
            display_status = 'expired'
        elif inst.current_status == 'verified' and days_left <= 30:
            display_status = 'expiring_soon'

    latest_cert = None
    if inst.current_cert_id:
        latest_cert = Certificate.query.get(inst.current_cert_id)

    logs = AuditLog.query.filter_by(instrument_id=inst.id).order_by(AuditLog.timestamp).all()

    return jsonify({
        'instrument': inst.to_dict(),
        'display_status': display_status,
        'days_left': days_left,
        'latest_certificate': latest_cert.to_dict() if latest_cert else None,
        'history': [l.to_dict() for l in logs],
    })
