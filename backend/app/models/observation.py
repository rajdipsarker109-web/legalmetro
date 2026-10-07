from app import db
from datetime import datetime


class Observation(db.Model):
    __tablename__ = 'observations'

    id = db.Column(db.String(36), primary_key=True)
    application_id = db.Column(db.String(36), db.ForeignKey('applications.id'), nullable=False)
    inspector_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    test_weights_used = db.Column(db.String(300))
    permissible_error_limit = db.Column(db.Numeric(10, 4))
    actual_error_observed = db.Column(db.Numeric(10, 4))
    error_within_limit = db.Column(db.Boolean)
    physical_condition = db.Column(db.Enum('good', 'damaged', 'tampered'))
    labels_compliant = db.Column(db.Boolean)
    previous_stamp_verified = db.Column(db.Boolean)
    overall_result = db.Column(db.Enum('verified', 'failed', 'conditionally_approved'))
    inspector_notes = db.Column(db.Text)
    photo_urls = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inspector = db.relationship('User', foreign_keys=[inspector_id])

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'inspector_id': self.inspector_id,
            'inspector': self.inspector.to_dict() if self.inspector else None,
            'test_weights_used': self.test_weights_used,
            'permissible_error_limit': float(self.permissible_error_limit) if self.permissible_error_limit is not None else None,
            'actual_error_observed': float(self.actual_error_observed) if self.actual_error_observed is not None else None,
            'error_within_limit': self.error_within_limit,
            'physical_condition': self.physical_condition,
            'labels_compliant': self.labels_compliant,
            'previous_stamp_verified': self.previous_stamp_verified,
            'overall_result': self.overall_result,
            'inspector_notes': self.inspector_notes,
            'photo_urls': self.photo_urls or [],
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
        }
