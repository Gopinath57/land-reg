from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, LandRecord, Document, Verification, AuditLog, db
from services import DuplicateDetector
from .auth import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@role_required('Administrator')
def index():
    users = User.query.order_by(User.created_at.desc()).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(25).all()
    record_count = LandRecord.query.count()
    doc_count = Document.query.count()
    ver_count = Verification.query.count()

    return render_template(
        'admin.html',
        users=users,
        recent_logs=recent_logs,
        record_count=record_count,
        doc_count=doc_count,
        ver_count=ver_count,
        active_tab='overview'
    )

@admin_bp.route('/admin/users/new', methods=['POST'])
@login_required
@role_required('Administrator')
def create_user():
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'Revenue Officer')
    dept = request.form.get('department', 'Revenue Dept')

    if not email or not password or not name:
        flash('Email, name, and password are required.', 'danger')
        return redirect(url_for('admin.index'))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash(f"User with email {email} already exists.", 'danger')
        return redirect(url_for('admin.index'))

    user = User(email=email, name=name, role=role, department=dept, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    AuditLog.log(
        'USER_CREATED',
        user_id=current_user.id,
        entity_type='User',
        entity_id=user.id,
        details=f"Created new staff user {user.name} ({user.email}) as {user.role}.",
        ip_address=request.remote_addr
    )
    flash(f"User {user.name} ({user.role}) created successfully.", 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('Administrator')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('admin.index'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = 'Activated' if user.is_active else 'Deactivated'
    AuditLog.log(
        'USER_STATUS_TOGGLED',
        user_id=current_user.id,
        entity_type='User',
        entity_id=user.id,
        details=f"User {user.email} status changed to {status_str}.",
        ip_address=request.remote_addr
    )
    flash(f"User {user.name} has been {status_str}.", 'info')
    return redirect(url_for('admin.index'))

@admin_bp.route('/admin/scan-all-duplicates', methods=['POST'])
@login_required
@role_required('Administrator')
def scan_all():
    result = DuplicateDetector.scan_all_records()
    AuditLog.log(
        'GLOBAL_DUPLICATE_SCAN',
        user_id=current_user.id,
        details=f"Global registry scan completed. Total checked: {result['total_scanned']}, Flagged: {result['flagged_count']}.",
        ip_address=request.remote_addr
    )
    flash(f"Registry-wide scan complete! {result['total_scanned']} records analyzed, {result['flagged_count']} flagged with duplicate risk.", 'info')
    return redirect(url_for('records.view_duplicates'))
