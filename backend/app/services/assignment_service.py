from app.models.jurisdiction import Jurisdiction


def assign_to_officer(instrument, preferred_type):
    query = Jurisdiction.query.filter_by(
        officer_type=preferred_type,
        district=instrument.usage_district,
    )
    if instrument.usage_state:
        query = query.filter_by(state=instrument.usage_state)

    jurisdictions = query.all()
    if preferred_type == 'gatc':
        for j in jurisdictions:
            cats = j.approved_categories or []
            if instrument.instrument_type in cats:
                return j.officer_id
        return None

    if jurisdictions:
        return jurisdictions[0].officer_id
    return None
