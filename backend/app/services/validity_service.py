from dateutil.relativedelta import relativedelta

VALIDITY_MONTHS = {
    'Non-Automatic Weighing Scale': 12,
    'Platform Scale': 12,
    'Fuel Dispenser': 12,
    'Water Meter': 24,
    'Energy Meter': 24,
    'Gas Meter': 24,
    'Clinical Thermometer': 12,
    'Taxi Meter': 12,
    'Moisture Meter': 12,
}


def compute_valid_until(instrument_type, issue_date):
    months = VALIDITY_MONTHS.get(instrument_type, 12)
    return issue_date + relativedelta(months=months)
