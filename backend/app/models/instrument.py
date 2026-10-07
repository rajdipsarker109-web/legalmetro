from app import db
from datetime import datetime


class Instrument(db.Model):
    __tablename__ = 'instruments'

    id = db.Column(db.String(36), primary_key=True)
    unique_instrument_id = db.Column(db.String(30), nullable=False, unique=True)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    instrument_type = db.Column(db.String(100), nullable=False)
    make = db.Column(db.String(150))
    model_name = db.Column(db.String(150))
    serial_number = db.Column(db.String(150))
    manufacturer_name = db.Column(db.String(200))
    usage_state = db.Column(db.String(100))
    usage_district = db.Column(db.String(100))
    usage_address = db.Column(db.Text)
    model_approval_cert_url = db.Column(db.Text)
    purchase_invoice_url = db.Column(db.Text)
    qr_code_url = db.Column(db.Text)
    current_status = db.Column(
        db.Enum('registered', 'pending_verification', 'verified', 'expired', 'failed', 'revoked'),
        default='registered'
    )
    current_cert_id = db.Column(db.String(36))
    cert_valid_until = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = db.relationship('Application', backref='instrument', lazy=True)
    certificates = db.relationship('Certificate', backref='instrument', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='instrument', lazy=True, order_by='AuditLog.timestamp')

    def to_dict(self):
        return {
            'id': self.id,
            'unique_instrument_id': self.unique_instrument_id,
            'owner_id': self.owner_id,
            'owner': self.owner.to_dict() if self.owner else None,
            'instrument_type': self.instrument_type,
            'make': self.make,
            'model_name': self.model_name,
            'serial_number': self.serial_number,
            'manufacturer_name': self.manufacturer_name,
            'usage_state': self.usage_state,
            'usage_district': self.usage_district,
            'usage_address': self.usage_address,
            'model_approval_cert_url': self.model_approval_cert_url,
            'purchase_invoice_url': self.purchase_invoice_url,
            'qr_code_url': self.qr_code_url,
            'current_status': self.current_status,
            'current_cert_id': self.current_cert_id,
            'cert_valid_until': self.cert_valid_until.isoformat() if self.cert_valid_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
