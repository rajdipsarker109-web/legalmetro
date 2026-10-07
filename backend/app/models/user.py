from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'lmo', 'gatc', 'business_owner'), nullable=False)
    phone = db.Column(db.String(15))
    organisation = db.Column(db.String(300))
    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    designation = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    instruments = db.relationship('Instrument', foreign_keys='Instrument.owner_id', backref='owner', lazy=True)
    applications_submitted = db.relationship('Application', foreign_keys='Application.applicant_id', backref='applicant', lazy=True)
    applications_assigned = db.relationship('Application', foreign_keys='Application.assigned_to_id', backref='assigned_officer', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    jurisdiction = db.relationship('Jurisdiction', backref='officer', uselist=False, foreign_keys='Jurisdiction.officer_id')

    def to_dict(self, include_sensitive=False):
        d = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'organisation': self.organisation,
            'state': self.state,
            'district': self.district,
            'designation': self.designation,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        return d
