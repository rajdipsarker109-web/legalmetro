import random
import uuid
from werkzeug.utils import secure_filename

STATE_CODES = {
    'Delhi': 'DL', 'Maharashtra': 'MH', 'Karnataka': 'KA', 'Tamil Nadu': 'TN',
    'Gujarat': 'GJ', 'Rajasthan': 'RJ', 'Uttar Pradesh': 'UP', 'West Bengal': 'WB',
    'Kerala': 'KL', 'Punjab': 'PB', 'Haryana': 'HR', 'Madhya Pradesh': 'MP',
}


def new_id():
    return str(uuid.uuid4())


def state_code(state_name):
    if not state_name:
        return 'IN'
    return STATE_CODES.get(state_name, state_name[:2].upper())


def generate_instrument_id(state_name, year=None):
    from datetime import datetime
    year = year or datetime.utcnow().year
    code = state_code(state_name)
    return f"LM-{code}-{year}-{random.randint(100000, 999999)}"


def generate_cert_number(state_name, year=None):
    from datetime import datetime
    from app.models.certificate import Certificate
    year = year or datetime.utcnow().year
    code = state_code(state_name)
    prefix = f"VC-{code}-{year}-"
    count = Certificate.query.filter(
        Certificate.certificate_number.like(f"{prefix}%")
    ).count()
    return f"{prefix}{str(count + 1).zfill(5)}"


def save_upload(file, folder, prefix=''):
    if not file or not file.filename:
        return None
    filename = secure_filename(f"{prefix}{file.filename}")
    path = folder / filename if hasattr(folder, '__truediv__') else f"{folder}/{filename}"
    if hasattr(folder, '__truediv__'):
        file.save(str(path))
        return filename
    import os
    full = os.path.join(folder, filename)
    file.save(full)
    return filename


INSTRUMENT_TYPES = [
    'Non-Automatic Weighing Scale', 'Platform Scale', 'Fuel Dispenser',
    'Water Meter', 'Energy Meter', 'Gas Meter', 'Clinical Thermometer',
    'Taxi Meter', 'Moisture Meter',
]

PERMISSIBLE_ERRORS = {
    'Non-Automatic Weighing Scale': 0.5,
    'Platform Scale': 0.5,
    'Fuel Dispenser': 0.3,
    'Water Meter': 2.0,
    'Energy Meter': 1.0,
    'Gas Meter': 1.5,
    'Clinical Thermometer': 0.2,
    'Taxi Meter': 0.5,
    'Moisture Meter': 1.0,
}
