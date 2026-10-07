from app import db
from datetime import datetime


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.String(36), primary_key=True)
    instrument_id = db.Column(db.String(36), db.ForeignKey('instruments.id'), nullable=False)
    applicant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    assigned_type = db.Column(db.Enum('lmo', 'gatc'))
    application_type = db.Column(db.Enum('new', 're_verification', 'post_repair'), nullable=False)
    status = db.Column(db.Enum(
        'submitted', 'under_review', 'docs_approved', 'docs_rejected',
        'inspection_scheduled', 'inspection_done', 'verified', 'rejected', 'failed'
    ), default='submitted')
    prev_cert_url = db.Column(db.Text)
    fee_amount = db.Column(db.Numeric(10, 2), default=500.00)
    fee_paid = db.Column(db.Boolean, default=False)
    fee_txn_id = db.Column(db.String(100))
    rejection_reason = db.Column(db.Text)
    inspection_date = db.Column(db.DateTime)
    inspection_type = db.Column(db.Enum('onsite', 'walkin'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    gatc_deadline = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    observations = db.relationship('Observation', backref='application', lazy=True)
    certificates = db.relationship('Certificate', backref='application', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'instrument_id': self.instrument_id,
            'instrument': self.instrument.to_dict() if self.instrument else None,
            'applicant_id': self.applicant_id,
            'applicant': self.applicant.to_dict() if self.applicant else None,
            'assigned_to_id': self.assigned_to_id,
            'assigned_officer': self.assigned_officer.to_dict() if self.assigned_officer else None,
            'assigned_type': self.assigned_type,
            'application_type': self.application_type,
            'status': self.status,
            'prev_cert_url': self.prev_cert_url,
            'fee_amount': float(self.fee_amount) if self.fee_amount else 500.0,
            'fee_paid': self.fee_paid,
            'fee_txn_id': self.fee_txn_id,
            'rejection_reason': self.rejection_reason,
            'inspection_date': self.inspection_date.isoformat() if self.inspection_date else None,
            'inspection_type': self.inspection_type,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'gatc_deadline': self.gatc_deadline.isoformat() if self.gatc_deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'observations': [o.to_dict() for o in self.observations],
            'certificates': [c.to_dict() for c in self.certificates],
        }
