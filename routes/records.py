from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import LandRecord, Document, Verification, AuditLog, db
from services import DuplicateDetector, RecordComparator
from .auth import role_required

records_bp = Blueprint('records', __name__)

@records_bp.route('/records')
@login_required
def list_records():
    query_str = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    district_filter = request.args.get('district', '').strip()
    type_filter = request.args.get('land_type', '').strip()
    duplicate_filter = request.args.get('duplicate_risk', '').strip()

    records_query = LandRecord.query

    if query_str:
        search_fmt = f"%{query_str}%"
        records_query = records_query.filter(
            (LandRecord.owner_name.ilike(search_fmt)) |
            (LandRecord.khasra_number.ilike(search_fmt)) |
            (LandRecord.survey_number.ilike(search_fmt)) |
            (LandRecord.parcel_id.ilike(search_fmt)) |
            (LandRecord.village.ilike(search_fmt))
        )

    if status_filter:
        records_query = records_query.filter(LandRecord.status == status_filter)

    if district_filter:
        records_query = records_query.filter(LandRecord.district == district_filter)

    if type_filter:
        records_query = records_query.filter(LandRecord.land_type == type_filter)

    if duplicate_filter:
        records_query = records_query.filter(LandRecord.duplicate_risk == duplicate_filter)

    records = records_query.order_by(LandRecord.updated_at.desc()).all()

    # Collect unique districts and types for dropdown filters
    districts = [r[0] for r in db.session.query(LandRecord.district).distinct().all() if r[0]]
    land_types = [r[0] for r in db.session.query(LandRecord.land_type).distinct().all() if r[0]]

    return render_template(
        'records.html',
        records=records,
        districts=districts,
        land_types=land_types,
        selected_q=query_str,
        selected_status=status_filter,
        selected_district=district_filter,
        selected_type=type_filter,
        selected_duplicate=duplicate_filter
    )

@records_bp.route('/records/new', methods=['GET', 'POST'])
@login_required
@role_required('Revenue Officer', 'Administrator')
def create_record():
    if request.method == 'POST':
        khasra = request.form.get('khasra_number', '').strip()
        survey = request.form.get('survey_number', '').strip()
        parcel = request.form.get('parcel_id', '').strip()
        owner = request.form.get('owner_name', '').strip()
        co_owners = request.form.get('co_owners', '').strip()
        father_name = request.form.get('father_or_husband_name', '').strip()
        aadhaar = request.form.get('aadhaar_masked', '').strip()
        district = request.form.get('district', '').strip()
        tehsil = request.form.get('tehsil', '').strip()
        village = request.form.get('village', '').strip()
        pincode = request.form.get('pincode', '').strip()
        land_type = request.form.get('land_type', 'Agricultural').strip()
        area_str = request.form.get('area_acres', '0').strip()
        val_str = request.form.get('market_value', '0').strip()
        mutation = request.form.get('mutation_number', '').strip()
        reg_date_str = request.form.get('registration_date', '').strip()
        north = request.form.get('north_boundary', '').strip()
        south = request.form.get('south_boundary', '').strip()
        east = request.form.get('east_boundary', '').strip()
        west = request.form.get('west_boundary', '').strip()
        linked_doc_id = request.form.get('linked_document_id', '').strip()

        if not khasra or not survey or not owner or not district or not village:
            flash('Please fill in all mandatory fields (Khasra, Survey, Owner, District, Village).', 'danger')
            return render_template('record_form.html', record=None)

        # Auto-generate parcel_id if blank
        if not parcel:
            clean_dist = district[:3].upper()
            parcel = f"LR-{clean_dist}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Check unique parcel ID
        existing = LandRecord.query.filter_by(parcel_id=parcel).first()
        if existing:
            parcel = f"{parcel}-{datetime.utcnow().strftime('%S')}"

        try:
            area_val = float(area_str)
        except ValueError:
            area_val = 0.0

        try:
            market_val = float(val_str)
        except ValueError:
            market_val = 0.0

        reg_date = None
        if reg_date_str:
            try:
                reg_date = datetime.strptime(reg_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        record = LandRecord(
            khasra_number=khasra,
            survey_number=survey,
            parcel_id=parcel,
            owner_name=owner,
            co_owners=co_owners,
            father_or_husband_name=father_name,
            aadhaar_masked=aadhaar,
            district=district,
            tehsil=tehsil,
            village=village,
            pincode=pincode,
            land_type=land_type,
            area_acres=area_val,
            market_value=market_val,
            mutation_number=mutation,
            registration_date=reg_date,
            north_boundary=north,
            south_boundary=south,
            east_boundary=east,
            west_boundary=west,
            status='Pending Verification',
            created_by_id=current_user.id
        )
        record.calculate_sqft()
        db.session.add(record)
        db.session.commit()

        # Link document if provided
        if linked_doc_id and linked_doc_id.isdigit():
            doc = Document.query.get(int(linked_doc_id))
            if doc:
                doc.record_id = record.id
                db.session.commit()
                # Run record comparison against linked document
                RecordComparator.compare_record_with_document(record.id, doc.id)

        # Run automated duplicate detector
        dup_res = DuplicateDetector.scan_record(record.id)

        AuditLog.log(
            'RECORD_CREATED',
            user_id=current_user.id,
            entity_type='LandRecord',
            entity_id=record.id,
            details=f"Digitized Land Record Parcel {record.parcel_id} for Owner {record.owner_name} (Khasra: {record.khasra_number}). Duplicate Risk: {dup_res['risk_level']}.",
            ip_address=request.remote_addr
        )

        flash(f"Land Record {record.parcel_id} successfully created and submitted for verification.", 'success')
        return redirect(url_for('records.view_record', record_id=record.id))

    # Pre-fill from query params (from OCR extraction)
    initial_data = {
        'khasra_number': request.args.get('khasra_number', ''),
        'survey_number': request.args.get('survey_number', ''),
        'owner_name': request.args.get('owner_name', ''),
        'father_or_husband_name': request.args.get('father_or_husband_name', ''),
        'co_owners': request.args.get('co_owners', ''),
        'district': request.args.get('district', ''),
        'tehsil': request.args.get('tehsil', ''),
        'village': request.args.get('village', ''),
        'area_acres': request.args.get('area_acres', ''),
        'market_value': request.args.get('market_value', ''),
        'registration_date': request.args.get('registration_date', ''),
        'north_boundary': request.args.get('north_boundary', ''),
        'south_boundary': request.args.get('south_boundary', ''),
        'east_boundary': request.args.get('east_boundary', ''),
        'west_boundary': request.args.get('west_boundary', ''),
        'linked_document_id': request.args.get('doc_id', '')
    }

    return render_template('record_form.html', record=None, prefill=initial_data)

@records_bp.route('/records/<int:record_id>')
@login_required
def view_record(record_id):
    record = LandRecord.query.get_or_404(record_id)
    dup_scan = DuplicateDetector.scan_record(record.id)
    comparator_result = None

    if record.documents:
        primary_doc = record.documents[0]
        comparator_result = RecordComparator.compare_record_with_document(record.id, primary_doc.id)

    audit_history = AuditLog.query.filter_by(entity_type='LandRecord', entity_id=record.id).order_by(AuditLog.timestamp.desc()).all()

    return render_template(
        'record_details.html',
        record=record,
        dup_scan=dup_scan,
        comparator_result=comparator_result,
        audit_history=audit_history
    )

@records_bp.route('/records/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Revenue Officer', 'Administrator')
def edit_record(record_id):
    record = LandRecord.query.get_or_404(record_id)

    if request.method == 'POST':
        record.khasra_number = request.form.get('khasra_number', '').strip()
        record.survey_number = request.form.get('survey_number', '').strip()
        record.owner_name = request.form.get('owner_name', '').strip()
        record.co_owners = request.form.get('co_owners', '').strip()
        record.father_or_husband_name = request.form.get('father_or_husband_name', '').strip()
        record.aadhaar_masked = request.form.get('aadhaar_masked', '').strip()
        record.district = request.form.get('district', '').strip()
        record.tehsil = request.form.get('tehsil', '').strip()
        record.village = request.form.get('village', '').strip()
        record.pincode = request.form.get('pincode', '').strip()
        record.land_type = request.form.get('land_type', 'Agricultural').strip()
        
        try:
            record.area_acres = float(request.form.get('area_acres', '0'))
        except ValueError:
            pass
        
        try:
            record.market_value = float(request.form.get('market_value', '0'))
        except ValueError:
            pass

        record.mutation_number = request.form.get('mutation_number', '').strip()
        reg_date_str = request.form.get('registration_date', '').strip()
        if reg_date_str:
            try:
                record.registration_date = datetime.strptime(reg_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        record.north_boundary = request.form.get('north_boundary', '').strip()
        record.south_boundary = request.form.get('south_boundary', '').strip()
        record.east_boundary = request.form.get('east_boundary', '').strip()
        record.west_boundary = request.form.get('west_boundary', '').strip()
        record.calculate_sqft()
        record.updated_at = datetime.utcnow()

        db.session.commit()

        # Re-run duplicate detection and document comparison
        DuplicateDetector.scan_record(record.id)
        if record.documents:
            RecordComparator.compare_record_with_document(record.id, record.documents[0].id)

        AuditLog.log(
            'RECORD_UPDATED',
            user_id=current_user.id,
            entity_type='LandRecord',
            entity_id=record.id,
            details=f"Record {record.parcel_id} details updated by {current_user.name}.",
            ip_address=request.remote_addr
        )

        flash(f"Record {record.parcel_id} updated successfully.", 'success')
        return redirect(url_for('records.view_record', record_id=record.id))

    return render_template('record_form.html', record=record)

@records_bp.route('/records/<int:record_id>/delete', methods=['POST'])
@login_required
@role_required('Administrator')
def delete_record(record_id):
    record = LandRecord.query.get_or_404(record_id)
    parcel_id = record.parcel_id
    db.session.delete(record)
    db.session.commit()

    AuditLog.log(
        'RECORD_DELETED',
        user_id=current_user.id,
        entity_type='LandRecord',
        entity_id=record_id,
        details=f"Record {parcel_id} deleted by Administrator {current_user.email}.",
        ip_address=request.remote_addr
    )
    flash(f"Record {parcel_id} has been permanently deleted.", 'info')
    return redirect(url_for('records.list_records'))

@records_bp.route('/records/<int:record_id>/scan-duplicates', methods=['POST'])
@login_required
def scan_duplicates_action(record_id):
    record = LandRecord.query.get_or_404(record_id)
    res = DuplicateDetector.scan_record(record.id)
    AuditLog.log(
        'DUPLICATE_SCAN_TRIGGERED',
        user_id=current_user.id,
        entity_type='LandRecord',
        entity_id=record.id,
        details=f"Manual duplicate check run for {record.parcel_id}. Result: {res['risk_level']} risk.",
        ip_address=request.remote_addr
    )
    flash(f"Duplicate scan completed: {res['risk_level']} risk level detected ({len(res['matches'])} potential conflicts).", 'info')
    return redirect(url_for('records.view_record', record_id=record.id))

@records_bp.route('/duplicates')
@login_required
def view_duplicates():
    flagged = LandRecord.query.filter(LandRecord.duplicate_risk.in_(['High', 'Medium', 'Low'])).all()
    high_count = sum(1 for r in flagged if r.duplicate_risk == 'High')
    medium_count = sum(1 for r in flagged if r.duplicate_risk == 'Medium')
    low_count = sum(1 for r in flagged if r.duplicate_risk == 'Low')

    return render_template(
        'duplicates.html',
        records=flagged,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count
    )

@records_bp.route('/mismatches')
@login_required
def view_mismatches():
    mismatched = LandRecord.query.filter_by(mismatch_detected=True).all()
    return render_template('mismatches.html', records=mismatched)
