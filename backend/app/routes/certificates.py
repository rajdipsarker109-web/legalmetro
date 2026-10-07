import os
from flask import Blueprint, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required
from app.models.certificate import Certificate

certificates_bp = Blueprint('certificates', __name__)


@certificates_bp.route('/certificates/<cert_id>', methods=['GET'])
@jwt_required()
def get_certificate(cert_id):
    cert = Certificate.query.get(cert_id)
    if not cert:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(cert.to_dict())


@certificates_bp.route('/certificates/<cert_id>/download', methods=['GET'])
def download_certificate(cert_id):
    cert = Certificate.query.get(cert_id)
    if not cert or not cert.certificate_url:
        return jsonify({'error': 'Not found'}), 404

    rel = cert.certificate_url.lstrip('/uploads/')
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], rel.replace('/', os.sep))
    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404

    mimetype = 'application/pdf' if path.endswith('.pdf') else 'text/html'
    return send_file(path, as_attachment=True, download_name=os.path.basename(path),
                     mimetype=mimetype)
