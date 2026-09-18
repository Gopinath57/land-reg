import os
from datetime import datetime, date
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User, LandRecord, Document, Verification, AuditLog
from routes import (
    auth_bp,
    dashboard_bp,
    records_bp,
    documents_bp,
    verification_bp,
    reports_bp,
    admin_bp
)
from services import DuplicateDetector, RecordComparator, OCRService

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required directories exist (safely handle read-only environments like Vercel)
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)
    except Exception:
        pass

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access the Land Digitization portal.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Jinja Template Filters
    @app.template_filter('currency')
    def format_currency(value):
        try:
            val = float(value)
            return f"Rs. {val:,.2f}"
        except (ValueError, TypeError):
            return "Rs. 0.00"

    @app.template_filter('format_date')
    def format_date(value, fmt='%d %b %Y'):
        if not value:
            return '-'
        if isinstance(value, (datetime, date)):
            return value.strftime(fmt)
        return str(value)

    @app.template_filter('status_badge')
    def status_badge(status):
        badges = {
            'Verified': 'badge-success',
            'Pending Verification': 'badge-warning',
            'Rejected': 'badge-danger',
            'Draft': 'badge-secondary',
            'Flagged Duplicate': 'badge-purple',
            'Flagged Mismatch': 'badge-orange'
        }
        return badges.get(status, 'badge-info')

    @app.template_filter('risk_badge')
    def risk_badge(risk):
        badges = {
            'High': 'badge-danger',
            'Medium': 'badge-warning',
            'Low': 'badge-info',
            'None': 'badge-success'
        }
        return badges.get(risk, 'badge-secondary')

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', code=404, message="The requested resource or page was not found."), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html', code=403, message="Access forbidden. You don't have privileges for this section."), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', code=500, message="An internal server error occurred."), 500

    return app

def seed_database(app):
    with app.app_context():
        db.create_all()

        # Seed Demo Accounts
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='Senior Registrar Admin',
                role='Administrator',
                department='Directorate of Land Records & Surveys'
            )
            admin.set_password('Demo@123')
            db.session.add(admin)

        revenue = User.query.filter_by(email='revenue@example.com').first()
        if not revenue:
            revenue = User(
                email='revenue@example.com',
                name='Priya Sharma (Revenue Officer)',
                role='Revenue Officer',
                department='Tehsil Revenue Circle'
            )
            revenue.set_password('Demo@123')
            db.session.add(revenue)

        verifier = User.query.filter_by(email='verify@example.com').first()
        if not verifier:
            verifier = User(
                email='verify@example.com',
                name='Anand Joshi (Verification Officer)',
                role='Verification Officer',
                department='Cadastral Settlement & Title Audit'
            )
            verifier.set_password('Demo@123')
            db.session.add(verifier)

        db.session.commit()

        # Seed Sample Land Records if table is empty
        if LandRecord.query.count() == 0:
            sample_records = [
                LandRecord(
                    khasra_number='142/3',
                    survey_number='SRV-2023-142',
                    parcel_id='LR-BHO-2023-0142',
                    owner_name='Rajesh Kumar Verma',
                    co_owners='Sunita Verma',
                    father_or_husband_name='Ramesh Verma',
                    aadhaar_masked='XXXX-XXXX-4912',
                    district='Bhopal',
                    tehsil='Huzur',
                    village='Kolar',
                    pincode='462042',
                    land_type='Agricultural',
                    area_acres=2.50,
                    market_value=4500000.0,
                    mutation_number='MUT-2023-901',
                    registration_date=date(2023, 11, 15),
                    north_boundary='Approach Road 30ft',
                    south_boundary='Plot 143 (Sharma)',
                    east_boundary='Open Agricultural Field',
                    west_boundary='Survey 141 (Govt Canal)',
                    status='Pending Verification',
                    created_by_id=revenue.id
                ),
                LandRecord(
                    khasra_number='142/3',
                    survey_number='SRV-2024-998',
                    parcel_id='LR-BHO-2024-0891',
                    owner_name='Rajesh K. Verma',
                    co_owners='Sunita Verma',
                    father_or_husband_name='Ramesh Verma',
                    aadhaar_masked='XXXX-XXXX-4912',
                    district='Bhopal',
                    tehsil='Huzur',
                    village='Kolar',
                    pincode='462042',
                    land_type='Agricultural',
                    area_acres=2.45,
                    market_value=4600000.0,
                    mutation_number='MUT-2024-112',
                    registration_date=date(2024, 1, 20),
                    north_boundary='Approach Road',
                    south_boundary='Plot 143',
                    east_boundary='Field',
                    west_boundary='Survey 141',
                    status='Pending Verification',
                    created_by_id=revenue.id
                ),
                LandRecord(
                    khasra_number='88/1A',
                    survey_number='SRV-2024-88A',
                    parcel_id='LR-JAI-2024-0088',
                    owner_name='Vikramaditya Singh',
                    co_owners='Anjali Singh',
                    father_or_husband_name='Mahendra Pratap Singh',
                    aadhaar_masked='XXXX-XXXX-8821',
                    district='Jaipur',
                    tehsil='Malviya Nagar',
                    village='Chandanpur',
                    pincode='302017',
                    land_type='Agricultural',
                    area_acres=3.40,
                    market_value=7500000.0,
                    mutation_number='MUT-2024-445',
                    registration_date=date(2024, 4, 10),
                    north_boundary='Survey No 87 (State Highway 12)',
                    south_boundary='Survey No 89 (Agricultural Land)',
                    east_boundary='Village Canal System',
                    west_boundary='Land of Suresh Chandra',
                    status='Verified',
                    created_by_id=revenue.id
                ),
                LandRecord(
                    khasra_number='314/2',
                    survey_number='SRV-2024-314',
                    parcel_id='LR-RAI-2024-0314',
                    owner_name='Ramesh Chand Sharma',
                    co_owners='Geeta Devi Sharma',
                    father_or_husband_name='Kailash Nath Sharma',
                    aadhaar_masked='XXXX-XXXX-3190',
                    district='Raipur',
                    tehsil='Bilaspur',
                    village='Rampur',
                    pincode='492001',
                    land_type='Residential',
                    area_acres=1.85,
                    market_value=1850000.0,
                    mutation_number='MUT-2024-781',
                    registration_date=date(2024, 2, 18),
                    north_boundary='PWD Main Road 40ft',
                    south_boundary='Khasra 315 (Govt Canal)',
                    east_boundary='Agricultural land of Mohan Das',
                    west_boundary='Primary School Playground',
                    status='Pending Verification',
                    created_by_id=revenue.id
                ),
                LandRecord(
                    khasra_number='512',
                    survey_number='SRV-2023-512',
                    parcel_id='LR-IND-2023-0512',
                    owner_name='Deepak Patel',
                    co_owners='',
                    father_or_husband_name='Sanjay Patel',
                    aadhaar_masked='XXXX-XXXX-1145',
                    district='Indore',
                    tehsil='Sanwer',
                    village='Dharampuri',
                    pincode='453551',
                    land_type='Commercial',
                    area_acres=0.95,
                    market_value=8200000.0,
                    mutation_number='MUT-2023-229',
                    registration_date=date(2023, 8, 14),
                    north_boundary='National Highway 52 Bypass',
                    south_boundary='Commercial Complex',
                    east_boundary='Service Lane',
                    west_boundary='Sub-Station Plot',
                    status='Verified',
                    created_by_id=revenue.id
                )
            ]

            for rec in sample_records:
                rec.calculate_sqft()
                db.session.add(rec)
            db.session.commit()

            # Seed a sample deed document linked to record 3
            sample_img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample_deed_seed.jpg')
            OCRService.create_sample_deed_image(sample_img_path, title='OFFICIAL REGISTERED TITLE DEED')
            doc_seed = Document(
                filename='sample_deed_seed.jpg',
                original_filename='Registered_Deed_88-1A.jpg',
                file_path=sample_img_path,
                file_type='Sale Deed',
                file_size_kb=85.4,
                record_id=sample_records[2].id,
                uploaded_by_id=revenue.id,
                ocr_status='Completed',
                ocr_confidence=95.2
            )
            parsed_entities = OCRService.parse_document_text(OCRService._generate_realistic_deed_text('Registered_Deed_88-1A.jpg', sample_img_path))
            doc_seed.extracted_text = OCRService._generate_realistic_deed_text('Registered_Deed_88-1A.jpg', sample_img_path)
            doc_seed.set_parsed_data(parsed_entities)
            db.session.add(doc_seed)
            db.session.commit()

            # Add an initial verification for the verified record
            v1 = Verification(
                record_id=sample_records[2].id,
                verified_by_id=verifier.id,
                status='Approved',
                remarks='Complete 30-year chain of title verified. Boundary survey coordinates match cadastral map. No encumbrances reported.',
                title_chain_verified=True,
                boundaries_verified=True,
                encumbrance_free=True,
                ocr_match_verified=True,
                duplicate_checked=True,
                verification_date=datetime.utcnow()
            )
            db.session.add(v1)

            # Audit logs
            AuditLog.log('SYSTEM_INITIALIZED', user_id=admin.id, details='Database tables initialized and demonstration records seeded.')
            AuditLog.log('RECORD_VERIFIED', user_id=verifier.id, entity_type='LandRecord', entity_id=sample_records[2].id, details='Parcel LR-JAI-2024-0088 formally approved and verified.')

            db.session.commit()

            # Run duplicate detector and record comparator on all seeded records
            DuplicateDetector.scan_all_records()
            RecordComparator.compare_record_with_document(sample_records[2].id, doc_seed.id)

app = create_app()

# Initialize tables and seed demo data on serverless/startup
try:
    with app.app_context():
        seed_database(app)
except Exception as _e:
    pass

if __name__ == '__main__':
    print("================================================================")
    print("   Land Record Digitization & Verification System Active")
    print("   Portal URL: http://127.0.0.1:5000")
    print("   Demo Logins:")
    print("     - Administrator:        admin@example.com   / Demo@123")
    print("     - Revenue Officer:      revenue@example.com / Demo@123")
    print("     - Verification Officer: verify@example.com  / Demo@123")
    print("================================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
