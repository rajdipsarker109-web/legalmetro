import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.application import Application
from app.models.observation import Observation
from app.utils.helpers import new_id, PERMISSIBLE_ERRORS
from app.utils.decorators import role_required
from app.services.assignment_service import assign_to_officer
from app.services.hash_service import create_audit_log
from app.services.notification_service import create_notification, send_email
from app.services.certificate_service import generate_certificate_pdf

applications_bp = Blueprint('applications', __name__)


@applications_bp.route('/applications/', methods=['POST'])
@role_required('business_owner')
def submit_application(current_user):
    data = request.get_json() or {}
    instrument_id = data.get('instrument_id')
    app_type = data.get('application_type', 'new')
    preferred = data.get('preferred_verifier', 'lmo')

    from app.models.instrument import Instrument
    inst = Instrument.query.get(instrument_id)
    if not inst or inst.owner_id != current_user.id:
        return jsonify({'error': 'Instrument not found'}), 404

    officer_id = assign_to_officer(inst, preferred)
    if not officer_id:
        return jsonify({'error': f'No {preferred.upper()} available for this district/category'}), 400

    gatc_deadline = None
    if preferred == 'gatc':
        gatc_deadline = (datetime.utcnow() + timedelta(days=15)).date()

    application = Application(
        id=new_id(),
        instrument_id=instrument_id,
        applicant_id=current_user.id,
        assigned_to_id=officer_id,
        assigned_type=preferred,
        application_type=app_type,
        status='submitted',
        fee_amount=500.00,
        fee_paid=data.get('fee_paid', True),
        fee_txn_id=data.get('fee_txn_id', f"TXN-{new_id()[:8].upper()}"),
        gatc_deadline=gatc_deadline,
    )
    inst.current_status = 'pending_verification'
    db.session.add(application)
    create_audit_log(inst.id, 'application_submitted', current_user.id,
                     f'Application submitted ({app_type})', {'application_id': application.id})
    officer = User.query.get(officer_id)
    create_notification(officer_id, 'application', 'New Application',
                        f'New {app_type} application for {inst.unique_instrument_id}')
    db.session.commit()
    return jsonify(application.to_dict()), 201


@applications_bp.route('/applications/', methods=['GET'])
@jwt_required()
def list_applications():
    user = User.query.get(get_jwt_identity())
    q = Application.query
    if user.role == 'business_owner':
        q = q.filter_by(applicant_id=user.id)
    elif user.role in ('lmo', 'gatc'):
        q = q.filter_by(assigned_to_id=user.id)
    elif user.role != 'super_admin':
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify([a.to_dict() for a in q.order_by(Application.submitted_at.desc()).all()])


@applications_bp.route('/applications/<app_id>', methods=['GET'])
@jwt_required()
def get_application(app_id):
    user = User.query.get(get_jwt_identity())
    app_obj = Application.query.get(app_id)
    if not app_obj:
        return jsonify({'error': 'Not found'}), 404
    if user.role == 'business_owner' and app_obj.applicant_id != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    if user.role in ('lmo', 'gatc') and app_obj.assigned_to_id != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify(app_obj.to_dict())


@applications_bp.route('/applications/<app_id>/review', methods=['PATCH'])
@role_required('lmo', 'gatc')
def review_docs(app_id, current_user):
    app_obj = Application.query.get(app_id)
    if not app_obj or app_obj.assigned_to_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json() or {}
    action = data.get('action')
    reason = data.get('reason', '')

    if action == 'approve':
        app_obj.status = 'docs_approved'
        msg = 'Documents approved. Inspection will be scheduled.'
    elif action == 'reject':
        app_obj.status = 'docs_rejected'
        app_obj.rejection_reason = reason
        app_obj.instrument.current_status = 'failed'
        msg = f'Documents rejected: {reason}'
    elif action == 'request_more':
        app_obj.status = 'under_review'
        msg = f'More documents requested: {reason}'
    else:
        return jsonify({'error': 'Invalid action'}), 400

    create_audit_log(app_obj.instrument_id, f'docs_{action}', current_user.id, msg)
    create_notification(app_obj.applicant_id, 'review', 'Application Update', msg)
    db.session.commit()
    return jsonify(app_obj.to_dict())


@applications_bp.route('/applications/<app_id>/schedule', methods=['POST'])
@role_required('lmo', 'gatc')
def schedule_inspection(app_id, current_user):
    app_obj = Application.query.get(app_id)
    if not app_obj or app_obj.assigned_to_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json() or {}
    inspection_date = data.get('inspection_date')
    if not inspection_date:
        return jsonify({'error': 'inspection_date required'}), 400

    app_obj.inspection_date = datetime.fromisoformat(inspection_date.replace('Z', ''))
    app_obj.inspection_type = data.get('inspection_type', 'onsite')
    app_obj.status = 'inspection_scheduled'

    msg = f'Inspection scheduled for {app_obj.inspection_date.strftime("%d %b %Y %H:%M")}'
    create_audit_log(app_obj.instrument_id, 'inspection_scheduled', current_user.id, msg)
    create_notification(app_obj.applicant_id, 'schedule', 'Inspection Scheduled', msg)
    db.session.commit()
    return jsonify(app_obj.to_dict())


@applications_bp.route('/applications/<app_id>/observations', methods=['POST'])
@role_required('lmo', 'gatc')
def record_observations(app_id, current_user):
    app_obj = Application.query.get(app_id)
    if not app_obj or app_obj.assigned_to_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404

    data = request.form
    upload_folder = current_app.config['UPLOAD_FOLDER']
    obs_dir = os.path.join(upload_folder, 'observations')
    os.makedirs(obs_dir, exist_ok=True)

    photo_urls = []
    for f in request.files.getlist('photos'):
        if f.filename:
            fn = secure_filename(f"obs_{new_id()[:8]}_{f.filename}")
            f.save(os.path.join(obs_dir, fn))
            photo_urls.append(f"/uploads/observations/{fn}")

    perm = float(data.get('permissible_error_limit') or PERMISSIBLE_ERRORS.get(
        app_obj.instrument.instrument_type, 0.5))
    actual = float(data.get('actual_error_observed') or 0)
    within = actual <= perm

    obs = Observation(
        id=new_id(),
        application_id=app_id,
        inspector_id=current_user.id,
        test_weights_used=data.get('test_weights_used'),
        permissible_error_limit=perm,
        actual_error_observed=actual,
        error_within_limit=within,
        physical_condition=data.get('physical_condition', 'good'),
        labels_compliant=data.get('labels_compliant') == 'true',
        previous_stamp_verified=data.get('previous_stamp_verified') == 'true',
        overall_result=data.get('overall_result', 'verified'),
        inspector_notes=data.get('inspector_notes'),
        photo_urls=photo_urls,
    )
    app_obj.status = 'inspection_done'
    db.session.add(obs)
    create_audit_log(app_obj.instrument_id, 'observation_recorded', current_user.id,
                     f'Inspection observation: {obs.overall_result}')
    db.session.commit()
    return jsonify(obs.to_dict()), 201


@applications_bp.route('/applications/<app_id>/certify', methods=['POST'])
@role_required('lmo', 'gatc')
def issue_certificate(app_id, current_user):
    app_obj = Application.query.get(app_id)
    if not app_obj or app_obj.assigned_to_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404

    if not app_obj.observations:
        return jsonify({'error': 'No observations recorded'}), 400
    latest = app_obj.observations[-1]
    if latest.overall_result != 'verified':
        return jsonify({'error': 'Observation result must be verified'}), 400

    cert = generate_certificate_pdf(
        app_obj.instrument, app_obj, current_user, app_obj.applicant
    )
    db.session.commit()
    return jsonify(cert.to_dict()), 201


@applications_bp.route('/applications/<app_id>/reject', methods=['PATCH'])
@role_required('lmo', 'gatc')
def reject_application(app_id, current_user):
    app_obj = Application.query.get(app_id)
    if not app_obj or app_obj.assigned_to_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json() or {}
    reason = data.get('reason', 'Rejected by officer')
    app_obj.status = 'rejected'
    app_obj.rejection_reason = reason
    app_obj.resolved_at = datetime.utcnow()
    app_obj.instrument.current_status = 'failed'

    create_audit_log(app_obj.instrument_id, 'application_rejected', current_user.id, reason)
    create_notification(app_obj.applicant_id, 'rejected', 'Application Rejected', reason)
    db.session.commit()
    return jsonify(app_obj.to_dict())
