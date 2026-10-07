"""Run: python seed.py — creates demo accounts, instruments, and audit chain."""
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models import User, Jurisdiction, Instrument, Application, Certificate, AuditLog
from app.routes.auth import hash_password
from app.services.hash_service import create_audit_log
from app.utils.helpers import new_id

app = create_app()


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Users
        admin = User(id=new_id(), name='System Admin', email='admin@legalmetro.gov.in',
                     password_hash=hash_password('Admin@123'), role='super_admin',
                     designation='Super Administrator')
        lmo_delhi = User(id=new_id(), name='Rajesh Kumar', email='lmo.delhi@legalmetro.gov.in',
                         password_hash=hash_password('Lmo@123'), role='lmo',
                         state='Delhi', district='Central Delhi',
                         designation='Legal Metrology Officer',
                         organisation='Delhi Legal Metrology Dept.')
        lmo_mumbai = User(id=new_id(), name='Priya Shah', email='lmo.mumbai@legalmetro.gov.in',
                          password_hash=hash_password('Lmo@123'), role='lmo',
                          state='Maharashtra', district='Mumbai City',
                          designation='Legal Metrology Officer',
                          organisation='Maharashtra Legal Metrology Dept.')
        gatc = User(id=new_id(), name='Weightech Labs', email='gatc@weightech.in',
                    password_hash=hash_password('Gatc@123'), role='gatc',
                    state='Delhi', district='Central Delhi',
                    designation='GATC Inspector', organisation='Weightech GATC Pvt Ltd')
        owner1 = User(id=new_id(), name='Amit Sharma', email='sharma@store.com',
                      password_hash=hash_password('Owner@123'), role='business_owner',
                      phone='9876543210', organisation='Sharma General Store',
                      state='Delhi', district='Central Delhi')
        owner2 = User(id=new_id(), name='Vikram Mehta', email='mehta@petrol.com',
                      password_hash=hash_password('Owner@123'), role='business_owner',
                      phone='9876543211', organisation='Mehta Petrol Station',
                      state='Maharashtra', district='Mumbai City')

        for u in [admin, lmo_delhi, lmo_mumbai, gatc, owner1, owner2]:
            db.session.add(u)

        # Jurisdictions
        db.session.add(Jurisdiction(id=new_id(), officer_id=lmo_delhi.id, officer_type='lmo',
                                    state='Delhi', district='Central Delhi'))
        db.session.add(Jurisdiction(id=new_id(), officer_id=lmo_mumbai.id, officer_type='lmo',
                                    state='Maharashtra', district='Mumbai City'))
        db.session.add(Jurisdiction(id=new_id(), officer_id=gatc.id, officer_type='gatc',
                                    state='Delhi', district='Central Delhi',
                                    approved_categories=['Non-Automatic Weighing Scale', 'Platform Scale']))
        db.session.flush()

        today = date.today()

        # Instrument 1 — verified, expiring in 10 days
        cert1_valid = today + timedelta(days=10)
        cert1_issue = cert1_valid - timedelta(days=365)
        inst1 = Instrument(
            id=new_id(), unique_instrument_id='LM-DL-2025-001001', owner_id=owner1.id,
            instrument_type='Non-Automatic Weighing Scale', make='Essae', model_name='DS-215',
            serial_number='SN-001001', manufacturer_name='Essae Teraoka Ltd.',
            usage_state='Delhi', usage_district='Central Delhi',
            usage_address='12, Connaught Place', current_status='verified',
            cert_valid_until=cert1_valid, qr_code_url='/uploads/qr/qr_LM-DL-2025-001001.png',
        )
        db.session.add(inst1)
        db.session.flush()
        app1 = Application(
            id=new_id(), instrument_id=inst1.id, applicant_id=owner1.id,
            assigned_to_id=lmo_delhi.id, assigned_type='lmo', application_type='new',
            status='verified', fee_paid=True, resolved_at=datetime.utcnow(),
        )
        db.session.add(app1)
        db.session.flush()
        cert1 = Certificate(
            id=new_id(), certificate_number='VC-DL-2025-00001',
            application_id=app1.id, instrument_id=inst1.id, issued_by_id=lmo_delhi.id,
            issuer_type='lmo', issue_date=cert1_issue, valid_until=cert1_valid,
            certificate_url='/uploads/certificates/VC-DL-2025-00001.html',
            verification_hash='seed_hash_001',
        )
        inst1.current_cert_id = cert1.id
        db.session.add(cert1)
        create_audit_log(inst1.id, 'registered', owner1.id, 'Instrument registered')
        create_audit_log(inst1.id, 'certificate_issued', lmo_delhi.id,
                         f'Certificate VC-DL-2025-00001 issued')

        # Instrument 2 — inspection scheduled
        inst2 = Instrument(
            id=new_id(), unique_instrument_id='LM-DL-2026-001002', owner_id=owner1.id,
            instrument_type='Platform Scale', make='Avery India', model_name='PS-500',
            serial_number='SN-001002', manufacturer_name='Avery India Ltd.',
            usage_state='Delhi', usage_district='Central Delhi',
            usage_address='12, Connaught Place', current_status='pending_verification',
            qr_code_url='/uploads/qr/qr_LM-DL-2026-001002.png',
        )
        db.session.add(inst2)
        db.session.flush()
        app2 = Application(
            id=new_id(), instrument_id=inst2.id, applicant_id=owner1.id,
            assigned_to_id=lmo_delhi.id, assigned_type='lmo', application_type='new',
            status='inspection_scheduled', fee_paid=True,
            inspection_date=datetime.utcnow() + timedelta(days=2),
            inspection_type='onsite',
        )
        db.session.add(app2)
        create_audit_log(inst2.id, 'registered', owner1.id, 'Instrument registered')
        create_audit_log(inst2.id, 'application_submitted', owner1.id, 'Application submitted')
        create_audit_log(inst2.id, 'inspection_scheduled', lmo_delhi.id, 'Inspection scheduled')

        # Instrument 3 — verified, 6 months left
        cert3_valid = today + timedelta(days=180)
        cert3_issue = cert3_valid - timedelta(days=365)
        inst3 = Instrument(
            id=new_id(), unique_instrument_id='LM-MH-2025-002001', owner_id=owner2.id,
            instrument_type='Fuel Dispenser', make='Tokheim', model_name='TD-200',
            serial_number='SN-002001', manufacturer_name='Tokheim India',
            usage_state='Maharashtra', usage_district='Mumbai City',
            usage_address='45, Marine Drive', current_status='verified',
            cert_valid_until=cert3_valid, qr_code_url='/uploads/qr/qr_LM-MH-2025-002001.png',
        )
        db.session.add(inst3)
        db.session.flush()
        app3 = Application(
            id=new_id(), instrument_id=inst3.id, applicant_id=owner2.id,
            assigned_to_id=lmo_mumbai.id, assigned_type='lmo', application_type='new',
            status='verified', fee_paid=True, resolved_at=datetime.utcnow(),
        )
        db.session.add(app3)
        db.session.flush()
        cert3 = Certificate(
            id=new_id(), certificate_number='VC-MH-2025-00001',
            application_id=app3.id, instrument_id=inst3.id, issued_by_id=lmo_mumbai.id,
            issuer_type='lmo', issue_date=cert3_issue, valid_until=cert3_valid,
            certificate_url='/uploads/certificates/VC-MH-2025-00001.html',
            verification_hash='seed_hash_002',
        )
        inst3.current_cert_id = cert3.id
        db.session.add(cert3)
        create_audit_log(inst3.id, 'registered', owner2.id, 'Instrument registered')
        create_audit_log(inst3.id, 'certificate_issued', lmo_mumbai.id,
                         'Certificate VC-MH-2025-00001 issued')

        # Instrument 4 — expired
        inst4 = Instrument(
            id=new_id(), unique_instrument_id='LM-MH-2024-002002', owner_id=owner2.id,
            instrument_type='Water Meter', make='Kranti', model_name='WM-100',
            serial_number='SN-002002', manufacturer_name='Kranti Meters',
            usage_state='Maharashtra', usage_district='Mumbai City',
            usage_address='45, Marine Drive', current_status='expired',
            cert_valid_until=today - timedelta(days=365),
            qr_code_url='/uploads/qr/qr_LM-MH-2024-002002.png',
        )
        db.session.add(inst4)
        create_audit_log(inst4.id, 'registered', owner2.id, 'Instrument registered')
        create_audit_log(inst4.id, 'certificate_expired', None, 'Certificate expired')

        db.session.commit()
        print('Seed complete!')
        print('   admin@legalmetro.gov.in / Admin@123')
        print('   lmo.delhi@legalmetro.gov.in / Lmo@123')
        print('   lmo.mumbai@legalmetro.gov.in / Lmo@123')
        print('   gatc@weightech.in / Gatc@123')
        print('   sharma@store.com / Owner@123')
        print('   mehta@petrol.com / Owner@123')


if __name__ == '__main__':
    seed()
