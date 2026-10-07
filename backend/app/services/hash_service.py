import hashlib
from app import db
from app.models.audit_log import AuditLog
from app.utils.helpers import new_id


def compute_hash(instrument_id, event_type, timestamp_str, previous_hash):
    data = f"{instrument_id}|{event_type}|{timestamp_str}|{previous_hash or ''}"
    return hashlib.sha256(data.encode()).hexdigest()


def create_audit_log(instrument_id, event_type, performed_by_id, description, metadata=None):
    last = AuditLog.query.filter_by(instrument_id=instrument_id).order_by(
        AuditLog.timestamp.desc()
    ).first()
    previous_hash = last.current_hash if last else None
    from datetime import datetime
    ts = datetime.utcnow()
    ts_str = ts.isoformat()
    current_hash = compute_hash(instrument_id, event_type, ts_str, previous_hash)
    log = AuditLog(
        id=new_id(),
        instrument_id=instrument_id,
        event_type=event_type,
        performed_by_id=performed_by_id,
        description=description,
        event_metadata=metadata,
        previous_hash=previous_hash,
        current_hash=current_hash,
        timestamp=ts,
    )
    db.session.add(log)
    return log
