from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from models import LandRecord, Document, Verification, AuditLog, db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

@dashboard_bp.route('/home')
def home():
    return render_template('index.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Key performance indicators
    total_records = LandRecord.query.count()
    pending_count = LandRecord.query.filter_by(status='Pending Verification').count()
    verified_count = LandRecord.query.filter_by(status='Verified').count()
    rejected_count = LandRecord.query.filter_by(status='Rejected').count()
    duplicate_count = LandRecord.query.filter(LandRecord.duplicate_risk.in_(['High', 'Medium'])).count()
    mismatch_count = LandRecord.query.filter_by(mismatch_detected=True).count()
    total_docs = Document.query.count()
    completed_ocr_docs = Document.query.filter_by(ocr_status='Completed').count()

    # District Breakdown
    district_data = db.session.query(
        LandRecord.district, func.count(LandRecord.id)
    ).group_by(LandRecord.district).all()

    # Land Type Breakdown
    type_data = db.session.query(
        LandRecord.land_type, func.count(LandRecord.id)
    ).group_by(LandRecord.land_type).all()

    # Recent Records
    recent_records = LandRecord.query.order_by(LandRecord.created_at.desc()).limit(8).all()

    # Recent Verifications
    recent_verifications = Verification.query.order_by(Verification.verification_date.desc()).limit(6).all()

    # Recent Audit Activities
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template(
        'dashboard.html',
        total_records=total_records,
        pending_count=pending_count,
        verified_count=verified_count,
        rejected_count=rejected_count,
        duplicate_count=duplicate_count,
        mismatch_count=mismatch_count,
        total_docs=total_docs,
        completed_ocr_docs=completed_ocr_docs,
        district_data=district_data,
        type_data=type_data,
        recent_records=recent_records,
        recent_verifications=recent_verifications,
        recent_logs=recent_logs
    )
