import csv
import io
from datetime import datetime, date
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.instrument import Instrument
from app.models.application import Application
from app.models.jurisdiction import Jurisdiction
from app.models.certificate import Certificate
from app.utils.helpers import new_id
from app.utils.decorators import role_required
from app.routes.auth import hash_password

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/stats', methods=['GET'])
@role_required('super_admin')
def admin_stats(current_user):
    today = date.today()
    month_start = today.replace(day=1)
    total = Instrument.query.count()
    verified_month = Certificate.query.filter(Certificate.issue_date >= month_start).count()
    pending = Application.query.filter(
        Application.status.in_(['submitted', 'under_review', 'docs_approved',
                                'inspection_scheduled', 'inspection_done'])
    ).count()
    expired = Instrument.query.filter(
        Instrument.current_status == 'expired'
    ).count() + Instrument.query.filter(
        Instrument.cert_valid_until < today,
        Instrument.current_status == 'verified'
    ).count()
    active_gatcs = User.query.filter_by(role='gatc', is_active=True).count()

    # Chart data: applications per month (last 12 months)
    apps_by_month = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        start = date(y, m, 1)
        end = date(y + (1 if m == 12 else 0), (m % 12) + 1, 1)
        count = Application.query.filter(
            Application.submitted_at >= datetime.combine(start, datetime.min.time()),
            Application.submitted_at < datetime.combine(end, datetime.min.time()),
        ).count()
        apps_by_month.append({'month': start.strftime('%b %Y'), 'count': count})

    # Instruments by type
    type_counts = db.session.query(
        Instrument.instrument_type, db.func.count(Instrument.id)
    ).group_by(Instrument.instrument_type).all()

    # Turnaround: avg days from submitted to resolved
    def avg_turnaround(officer_type):
        apps = Application.query.filter_by(
            assigned_type=officer_type, status='verified'
        ).filter(Application.resolved_at.isnot(None)).all()
        if not apps:
            return 0
        total_days = sum((a.resolved_at - a.submitted_at).days for a in apps)
        return round(total_days / len(apps), 1)

    recent = Application.query.order_by(Application.submitted_at.desc()).limit(10).all()

    return jsonify({
        'total_instruments': total,
        'verified_this_month': verified_month,
        'pending_applications': pending,
        'expired_instruments': expired,
        'active_gatcs': active_gatcs,
        'apps_by_month': apps_by_month,
        'instruments_by_type': [{'type': t, 'count': c} for t, c in type_counts],
        'turnaround': {'lmo': avg_turnaround('lmo'), 'gatc': avg_turnaround('gatc')},
        'recent_applications': [a.to_dict() for a in recent],
    })


@admin_bp.route('/instruments', methods=['GET'])
@role_required('super_admin')
def admin_instruments(current_user):
    q = Instrument.query
    if request.args.get('state'):
        q = q.filter_by(usage_state=request.args.get('state'))
    if request.args.get('district'):
        q = q.filter_by(usage_district=request.args.get('district'))
    if request.args.get('status'):
        q = q.filter_by(current_status=request.args.get('status'))
    if request.args.get('type'):
        q = q.filter_by(instrument_type=request.args.get('type'))
    if request.args.get('q'):
        term = f"%{request.args.get('q')}%"
        q = q.join(User, Instrument.owner_id == User.id).filter(
            db.or_(
                Instrument.unique_instrument_id.like(term),
                Instrument.serial_number.like(term),
                User.name.like(term),
                User.organisation.like(term),
            )
        )
    return jsonify([i.to_dict() for i in q.order_by(Instrument.created_at.desc()).all()])


@admin_bp.route('/users', methods=['GET'])
@role_required('super_admin')
def list_users(current_user):
    role = request.args.get('role')
    q = User.query.filter(User.role.in_(['lmo', 'gatc', 'super_admin']))
    if role:
        q = q.filter_by(role=role)
    users = []
    for u in q.all():
        d = u.to_dict()
        if u.jurisdiction:
            d['jurisdiction'] = u.jurisdiction.to_dict()
        users.append(d)
    return jsonify(users)


@admin_bp.route('/users/lmo', methods=['POST'])
@role_required('super_admin')
def create_lmo(current_user):
    data = request.get_json() or {}
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email exists'}), 409

    user = User(
        id=new_id(), name=data['name'], email=data['email'],
        password_hash=hash_password(data['password']),
        role='lmo', state=data.get('state'), district=data.get('district'),
        designation=data.get('designation', 'Legal Metrology Officer'),
        organisation=data.get('organisation', 'State Legal Metrology Dept.'),
    )
    db.session.add(user)
    j = Jurisdiction(
        id=new_id(), officer_id=user.id, officer_type='lmo',
        state=data.get('state'), district=data.get('district'),
    )
    db.session.add(j)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@admin_bp.route('/users/gatc', methods=['POST'])
@role_required('super_admin')
def create_gatc(current_user):
    data = request.get_json() or {}
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email exists'}), 409

    user = User(
        id=new_id(), name=data['name'], email=data['email'],
        password_hash=hash_password(data['password']),
        role='gatc', state=data.get('state'), district=data.get('district'),
        designation=data.get('designation', 'GATC Inspector'),
        organisation=data.get('organisation'),
    )
    db.session.add(user)
    j = Jurisdiction(
        id=new_id(), officer_id=user.id, officer_type='gatc',
        state=data.get('state'), district=data.get('district'),
        approved_categories=data.get('approved_categories', []),
    )
    db.session.add(j)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@admin_bp.route('/reports/export', methods=['GET'])
@role_required('super_admin')
def export_report(current_user):
    report_type = request.args.get('type', 'instruments')
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'expired':
        today = date.today()
        rows = Instrument.query.filter(
            db.or_(
                Instrument.current_status == 'expired',
                db.and_(Instrument.cert_valid_until < today,
                          Instrument.current_status == 'verified')
            )
        ).all()
        writer.writerow(['Instrument ID', 'Type', 'Owner', 'Status', 'Valid Until'])
        for i in rows:
            writer.writerow([
                i.unique_instrument_id, i.instrument_type,
                i.owner.name if i.owner else '', i.current_status,
                i.cert_valid_until,
            ])
    elif report_type == 'pending':
        rows = Application.query.filter(
            Application.status.notin_(['verified', 'rejected', 'failed'])
        ).all()
        writer.writerow(['App ID', 'Instrument', 'Type', 'Status', 'Submitted'])
        for a in rows:
            writer.writerow([
                a.id, a.instrument.unique_instrument_id if a.instrument else '',
                a.application_type, a.status, a.submitted_at,
            ])
    else:
        rows = Instrument.query.all()
        writer.writerow(['Instrument ID', 'Type', 'Owner', 'State', 'District', 'Status', 'Valid Until'])
        for i in rows:
            writer.writerow([
                i.unique_instrument_id, i.instrument_type,
                i.owner.name if i.owner else '', i.usage_state, i.usage_district,
                i.current_status, i.cert_valid_until,
            ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename=legalmetro_{report_type}.csv'
    return resp
