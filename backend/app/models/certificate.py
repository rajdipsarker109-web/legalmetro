from app import db
from datetime import datetime


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.String(36), primary_key=True)
    certificate_number = db.Column(db.String(30), nullable=False, unique=True)
    application_id = db.Column(db.String(36), db.ForeignKey('applications.id'), nullable=False)
    instrument_id = db.Column(db.String(36), db.ForeignKey('instruments.id'), nullable=False)
    issued_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    issuer_type = db.Column(db.Enum('lmo', 'gatc'))
    issue_date = db.Column(db.Date, nullable=False)
    valid_until = db.Column(db.Date, nullable=False)
    certificate_url = db.Column(db.Text)
    qr_embed_url = db.Column(db.Text)
    verification_hash = db.Column(db.String(64))
    is_revoked = db.Column(db.Boolean, default=False)
    revoke_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    issued_by = db.relationship('User', foreign_keys=[issued_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'certificate_number': self.certificate_number,
            'application_id': self.application_id,
            'instrument_id': self.instrument_id,
            'issued_by_id': self.issued_by_id,
            'issued_by': self.issued_by.to_dict() if self.issued_by else None,
            'issuer_type': self.issuer_type,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'certificate_url': self.certificate_url,
            'qr_embed_url': self.qr_embed_url,
            'verification_hash': self.verification_hash,
            'is_revoked': self.is_revoked,
            'revoke_reason': self.revoke_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
