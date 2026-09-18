import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, Response, make_response
from flask_login import login_required
from sqlalchemy import func
from models import LandRecord, Document, Verification, AuditLog, db
from services import DuplicateDetector

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def report_center():
    # Overall summary metrics
    total_records = LandRecord.query.count()
    verified_records = LandRecord.query.filter_by(status='Verified').count()
    pending_records = LandRecord.query.filter_by(status='Pending Verification').count()
    rejected_records = LandRecord.query.filter_by(status='Rejected').count()
    duplicate_records = LandRecord.query.filter(LandRecord.duplicate_risk.in_(['High', 'Medium'])).count()
    mismatch_records = LandRecord.query.filter_by(mismatch_detected=True).count()

    # District Statistics
    district_summary = db.session.query(
        LandRecord.district,
        func.count(LandRecord.id).label('total'),
        func.sum(case_col(LandRecord.status == 'Verified', 1, 0)).label('verified'),
        func.sum(case_col(LandRecord.status == 'Pending Verification', 1, 0)).label('pending'),
        func.sum(case_col(LandRecord.duplicate_risk.in_(['High', 'Medium']), 1, 0)).label('duplicates'),
        func.sum(LandRecord.area_acres).label('total_acres'),
        func.sum(LandRecord.market_value).label('total_val')
    ).group_by(LandRecord.district).all()

    # Land Type summary
    type_summary = db.session.query(
        LandRecord.land_type,
        func.count(LandRecord.id),
        func.sum(LandRecord.area_acres)
    ).group_by(LandRecord.land_type).all()

    # Verification officers performance
    verifier_stats = db.session.query(
        Verification.verified_by_id,
        func.count(Verification.id),
        func.sum(case_col(Verification.status == 'Approved', 1, 0)),
        func.sum(case_col(Verification.status == 'Rejected', 1, 0))
    ).group_by(Verification.verified_by_id).all()

    return render_template(
        'reports.html',
        total_records=total_records,
        verified_records=verified_records,
        pending_records=pending_records,
        rejected_records=rejected_records,
        duplicate_records=duplicate_records,
        mismatch_records=mismatch_records,
        district_summary=district_summary,
        type_summary=type_summary,
        verifier_stats=verifier_stats
    )

def case_col(condition, val_true, val_false):
    return db.case((condition, val_true), else_=val_false)

@reports_bp.route('/reports/export-records')
@login_required
def export_records_csv():
    records = LandRecord.query.order_by(LandRecord.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Parcel ID', 'Khasra Number', 'Survey Number', 'Owner Name', 'Co-Owners',
        'Father/Husband Name', 'District', 'Tehsil', 'Village', 'Land Type',
        'Area (Acres)', 'Area (Sq Ft)', 'Market Value (INR)', 'Status',
        'Duplicate Risk', 'Mismatch Detected', 'Created At'
    ])

    for r in records:
        writer.writerow([
            r.parcel_id, r.khasra_number, r.survey_number, r.owner_name, r.co_owners or '',
            r.father_or_husband_name or '', r.district, r.tehsil, r.village, r.land_type,
            r.area_acres, r.area_sqft, r.market_value, r.status,
            r.duplicate_risk, 'YES' if r.mismatch_detected else 'NO',
            r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
        ])

    csv_data = output.getvalue()
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f"attachment; filename=Land_Records_Export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response

@reports_bp.route('/reports/export-audit')
@login_required
def export_audit_csv():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'User ID', 'User Email', 'Action', 'Entity Type', 'Entity ID', 'Details', 'IP Address'])

    for l in logs:
        u_email = l.user.email if l.user else 'System'
        writer.writerow([
            l.id, l.timestamp.strftime('%Y-%m-%d %H:%M:%S'), l.user_id or '',
            u_email, l.action, l.entity_type or '', l.entity_id or '',
            l.details or '', l.ip_address or ''
        ])

    csv_data = output.getvalue()
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f"attachment; filename=Audit_Trail_Export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response
