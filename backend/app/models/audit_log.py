from app import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True)
    instrument_id = db.Column(db.String(36), db.ForeignKey('instruments.id'), nullable=False)
    event_type = db.Column(db.String(60), nullable=False)
    performed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    event_metadata = db.Column('metadata', db.JSON)
    previous_hash = db.Column(db.String(64))
    current_hash = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    performed_by = db.relationship('User', foreign_keys=[performed_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'instrument_id': self.instrument_id,
            'event_type': self.event_type,
            'performed_by_id': self.performed_by_id,
            'performed_by': self.performed_by.to_dict() if self.performed_by else None,
            'description': self.description,
            'metadata': self.event_metadata,
            'previous_hash': self.previous_hash,
            'current_hash': self.current_hash,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
