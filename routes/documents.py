import os
import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Document, LandRecord, AuditLog, db
from services import OCRService, RecordComparator
from .auth import role_required

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/documents')
@login_required
def list_documents():
    docs = Document.query.order_by(Document.created_at.desc()).all()
    return render_template('upload.html', documents=docs, active_tab='library')

@documents_bp.route('/documents/upload', methods=['GET', 'POST'])
@login_required
@role_required('Revenue Officer', 'Administrator')
def upload_document():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Please select a file to upload.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            orig_filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            saved_filename = f"{timestamp}_{orig_filename}"
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, saved_filename)
            file.save(file_path)

            file_size_kb = round(os.path.getsize(file_path) / 1024.0, 2)
            doc_type = request.form.get('file_type', 'Sale Deed')
            linked_record_id = request.form.get('record_id')

            document = Document(
                filename=saved_filename,
                original_filename=orig_filename,
                file_path=file_path,
                file_type=doc_type,
                file_size_kb=file_size_kb,
                record_id=int(linked_record_id) if linked_record_id and linked_record_id.isdigit() else None,
                uploaded_by_id=current_user.id,
                ocr_status='Processing'
            )
            db.session.add(document)
            db.session.commit()

            # Execute OCR service
            ocr_result = OCRService.process_file(file_path, saved_filename)
            document.ocr_status = ocr_result['status']
            document.ocr_confidence = ocr_result['confidence']
            document.extracted_text = ocr_result['extracted_text']
            document.set_parsed_data(ocr_result['entities'])
            db.session.commit()

            # If linked to a record, run comparator
            if document.record_id:
                RecordComparator.compare_record_with_document(document.record_id, document.id)

            AuditLog.log(
                'DOCUMENT_UPLOAD_OCR',
                user_id=current_user.id,
                entity_type='Document',
                entity_id=document.id,
                details=f"Uploaded document {orig_filename} ({doc_type}, {file_size_kb} KB). OCR confidence: {document.ocr_confidence}%.",
                ip_address=request.remote_addr
            )

            flash(f"Document {orig_filename} uploaded and OCR extracted successfully (Confidence: {document.ocr_confidence}%).", 'success')
            return redirect(url_for('documents.ocr_result', document_id=document.id))

        else:
            flash('Invalid file format. Allowed extensions: PDF, PNG, JPG, JPEG, TIFF, TXT.', 'danger')
            return redirect(request.url)

    docs = Document.query.order_by(Document.created_at.desc()).all()
    records = LandRecord.query.order_by(LandRecord.parcel_id).all()
    return render_template('upload.html', documents=docs, records=records, active_tab='upload')

@documents_bp.route('/documents/<int:document_id>/ocr', methods=['POST'])
@login_required
def trigger_ocr(document_id):
    document = Document.query.get_or_404(document_id)
    ocr_result = OCRService.process_file(document.file_path, document.filename)

    document.ocr_status = ocr_result['status']
    document.ocr_confidence = ocr_result['confidence']
    document.extracted_text = ocr_result['extracted_text']
    document.set_parsed_data(ocr_result['entities'])
    db.session.commit()

    if document.record_id:
        RecordComparator.compare_record_with_document(document.record_id, document.id)

    AuditLog.log(
        'OCR_REPROCESSED',
        user_id=current_user.id,
        entity_type='Document',
        entity_id=document.id,
        details=f"Re-processed OCR for {document.original_filename}. Confidence: {document.ocr_confidence}%.",
        ip_address=request.remote_addr
    )
    flash(f"OCR re-processing completed with {document.ocr_confidence}% confidence.", 'success')
    return redirect(url_for('documents.ocr_result', document_id=document.id))

@documents_bp.route('/documents/<int:document_id>/ocr-result')
@login_required
def ocr_result(document_id):
    document = Document.query.get_or_404(document_id)
    parsed = document.parsed_data
    return render_template('ocr_result.html', document=document, entities=parsed)

@documents_bp.route('/documents/<int:document_id>/download')
@login_required
def download_file(document_id):
    document = Document.query.get_or_404(document_id)
    if os.path.exists(document.file_path):
        return send_file(document.file_path, download_name=document.original_filename, as_attachment=False)
    flash('Requested document file was not found on the server.', 'danger')
    return redirect(url_for('documents.list_documents'))

@documents_bp.route('/documents/generate-sample')
@login_required
@role_required('Revenue Officer', 'Administrator')
def generate_sample_deed():
    sample_type = request.args.get('type', 'deed')
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"sample_{sample_type}_{timestamp}.jpg"
    file_path = os.path.join(upload_dir, filename)

    title = 'OFFICIAL REGISTERED TITLE DEED'
    if sample_type == 'patta':
        title = 'CERTIFICATE OF PATTA ALLOTMENT'
    elif sample_type == 'discrepancy':
        title = 'DEED OF ABSOLUTE SALE (AMENDED)'

    success = OCRService.create_sample_deed_image(file_path, title=title)
    if success:
        file_size_kb = round(os.path.getsize(file_path) / 1024.0, 2)
        doc = Document(
            filename=filename,
            original_filename=f"Registered_Deed_{sample_type.capitalize()}.jpg",
            file_path=file_path,
            file_type='Sale Deed' if sample_type != 'patta' else 'Patta',
            file_size_kb=file_size_kb,
            uploaded_by_id=current_user.id,
            ocr_status='Processing'
        )
        db.session.add(doc)
        db.session.commit()

        # Run OCR
        ocr_result = OCRService.process_file(file_path, filename)
        doc.ocr_status = ocr_result['status']
        doc.ocr_confidence = ocr_result['confidence']
        doc.extracted_text = ocr_result['extracted_text']
        doc.set_parsed_data(ocr_result['entities'])
        db.session.commit()

        AuditLog.log(
            'SAMPLE_DOCUMENT_GENERATED',
            user_id=current_user.id,
            entity_type='Document',
            entity_id=doc.id,
            details=f"Generated and OCR-extracted sample test deed: {doc.original_filename}.",
            ip_address=request.remote_addr
        )
        flash(f"Sample test deed successfully generated and processed with OCR (Confidence: {doc.ocr_confidence}%).", 'success')
        return redirect(url_for('documents.ocr_result', document_id=doc.id))
    else:
        flash('Failed to generate sample document image.', 'danger')
        return redirect(url_for('documents.list_documents'))
