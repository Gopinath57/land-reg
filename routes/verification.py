from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import LandRecord, Verification, AuditLog, db
from services import DuplicateDetector, RecordComparator
from .auth import role_required

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/verification')
@login_required
@role_required('Verification Officer', 'Administrator')
def queue():
    pending_records = LandRecord.query.filter_by(status='Pending Verification').order_by(LandRecord.created_at.asc()).all()
    flagged_duplicates = LandRecord.query.filter_by(status='Flagged Duplicate').order_by(LandRecord.created_at.asc()).all()
    flagged_mismatches = LandRecord.query.filter_by(status='Flagged Mismatch').order_by(LandRecord.created_at.asc()).all()
    
    verified_records = LandRecord.query.filter_by(status='Verified').order_by(LandRecord.updated_at.desc()).limit(15).all()
    rejected_records = LandRecord.query.filter_by(status='Rejected').order_by(LandRecord.updated_at.desc()).limit(15).all()

    return render_template(
        'verification.html',
        pending_records=pending_records,
        flagged_duplicates=flagged_duplicates,
        flagged_mismatches=flagged_mismatches,
        verified_records=verified_records,
        rejected_records=rejected_records
    )

@verification_bp.route('/verification/<int:record_id>', methods=['GET', 'POST'])
@login_required
@role_required('Verification Officer', 'Administrator')
def review_record(record_id):
    record = LandRecord.query.get_or_404(record_id)
    dup_scan = DuplicateDetector.scan_record(record.id)
    comparator_result = None

    if record.documents:
        primary_doc = record.documents[0]
        comparator_result = RecordComparator.compare_record_with_document(record.id, primary_doc.id)

    if request.method == 'POST':
        action = request.form.get('action') # 'Approved', 'Rejected', 'Needs Clarification'
        remarks = request.form.get('remarks', '').strip()
        chk_title = bool(request.form.get('title_chain_verified'))
        chk_boundaries = bool(request.form.get('boundaries_verified'))
        chk_encumbrance = bool(request.form.get('encumbrance_free'))
        chk_ocr = bool(request.form.get('ocr_match_verified'))
        chk_duplicate = bool(request.form.get('duplicate_checked'))

        if not remarks:
            flash('Remarks are mandatory for verification audit trail.', 'danger')
            return redirect(request.url)

        ver = Verification(
            record_id=record.id,
            verified_by_id=current_user.id,
            status=action,
            remarks=remarks,
            title_chain_verified=chk_title,
            boundaries_verified=chk_boundaries,
            encumbrance_free=chk_encumbrance,
            ocr_match_verified=chk_ocr,
            duplicate_checked=chk_duplicate
        )
        db.session.add(ver)

        if action == 'Approved':
            record.status = 'Verified'
            flash_msg = f"Record {record.parcel_id} has been formally VERIFIED and approved."
            flash_cat = 'success'
        elif action == 'Rejected':
            record.status = 'Rejected'
            flash_msg = f"Record {record.parcel_id} has been REJECTED."
            flash_cat = 'danger'
        else:
            record.status = 'Pending Verification'
            flash_msg = f"Record {record.parcel_id} sent back for clarification."
            flash_cat = 'warning'

        record.updated_at = datetime.utcnow()
        db.session.commit()

        AuditLog.log(
            f"RECORD_VERIFICATION_{action.upper()}",
            user_id=current_user.id,
            entity_type='LandRecord',
            entity_id=record.id,
            details=f"Verification decision '{action}' recorded by {current_user.name} ({current_user.role}). Remarks: {remarks}",
            ip_address=request.remote_addr
        )

        flash(flash_msg, flash_cat)
        return redirect(url_for('verification.queue'))

    return render_template(
        'record_details.html',
        record=record,
        dup_scan=dup_scan,
        comparator_result=comparator_result,
        verification_mode=True
    )
