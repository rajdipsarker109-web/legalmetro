from app import db
from datetime import datetime


class Jurisdiction(db.Model):
    __tablename__ = 'jurisdictions'

    id = db.Column(db.String(36), primary_key=True)
    officer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    officer_type = db.Column(db.Enum('lmo', 'gatc'), nullable=False)
    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    taluka = db.Column(db.String(100))
    approved_categories = db.Column(db.JSON)  # GATC only
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'officer_id': self.officer_id,
            'officer_type': self.officer_type,
            'state': self.state,
            'district': self.district,
            'taluka': self.taluka,
            'approved_categories': self.approved_categories,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
