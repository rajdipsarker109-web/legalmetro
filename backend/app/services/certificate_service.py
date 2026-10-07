import os
import base64
import hashlib
from datetime import date
from flask import current_app, render_template
from app import db
from app.models.certificate import Certificate
from app.utils.helpers import new_id, generate_cert_number
from app.services.validity_service import compute_valid_until
from app.services.hash_service import create_audit_log, compute_hash
from app.services.notification_service import create_notification, send_email
import qrcode
from io import BytesIO


def _qr_base64(verify_url):
    qr = qrcode.make(verify_url)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


def generate_certificate_pdf(instrument, application, officer, owner):
    issue_date = date.today()
    valid_until = compute_valid_until(instrument.instrument_type, issue_date)
    cert_number = generate_cert_number(instrument.usage_state, issue_date.year)
    frontend_url = current_app.config['FRONTEND_URL']
    verify_url = f"{frontend_url}/verify.html?id={instrument.unique_instrument_id}"
    qr_b64 = _qr_base64(verify_url)

    context = {
        'certificate_number': cert_number,
        'instrument': instrument,
        'owner': owner,
        'officer': officer,
        'issue_date': issue_date.strftime('%d %b %Y'),
        'valid_until': valid_until.strftime('%d %b %Y'),
        'qr_base64': qr_b64,
        'verify_url': verify_url,
    }

    upload_folder = current_app.config['UPLOAD_FOLDER']
    cert_dir = os.path.join(upload_folder, 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    pdf_filename = f"{cert_number}.pdf"
    pdf_path = os.path.join(cert_dir, pdf_filename)
    rel_url = f"/uploads/certificates/{pdf_filename}"

    html = render_template('certificate.html', **context)
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(pdf_path)
    except Exception:
        html_path = os.path.join(cert_dir, f"{cert_number}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        rel_url = f"/uploads/certificates/{cert_number}.html"

    verification_hash = hashlib.sha256(
        f"{cert_number}{instrument.unique_instrument_id}{issue_date}".encode()
    ).hexdigest()

    cert = Certificate(
        id=new_id(),
        certificate_number=cert_number,
        application_id=application.id,
        instrument_id=instrument.id,
        issued_by_id=officer.id,
        issuer_type=officer.role,
        issue_date=issue_date,
        valid_until=valid_until,
        certificate_url=rel_url,
        qr_embed_url=verify_url,
        verification_hash=verification_hash,
    )
    db.session.add(cert)

    instrument.current_status = 'verified'
    instrument.current_cert_id = cert.id
    instrument.cert_valid_until = valid_until

    application.status = 'verified'
    application.resolved_at = __import__('datetime').datetime.utcnow()

    create_audit_log(
        instrument.id, 'certificate_issued', officer.id,
        f'Certificate {cert_number} issued', {'cert_number': cert_number}
    )
    create_notification(
        owner.id, 'certificate', 'Certificate Issued',
        f'Certificate {cert_number} issued for {instrument.unique_instrument_id}. Valid until {valid_until}.'
    )
    send_email(
        owner.email, 'LegalMetro — Certificate Issued',
        f'Your certificate {cert_number} for instrument {instrument.unique_instrument_id} has been issued.'
    )
    return cert
