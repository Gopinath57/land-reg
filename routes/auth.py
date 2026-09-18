from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, AuditLog, db

auth_bp = Blueprint('auth', __name__)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in roles and not current_user.is_admin:
                flash('You do not have permission to access this resource.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('login.html')

            login_user(user, remember=remember)
            AuditLog.log('USER_LOGIN', user_id=user.id, details=f"User {user.email} ({user.role}) logged in successfully.", ip_address=request.remote_addr)
            flash(f"Welcome back, {user.name}! Logged in as {user.role}.", 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    uid = current_user.id
    uemail = current_user.email
    logout_user()
    AuditLog.log('USER_LOGOUT', user_id=uid, details=f"User {uemail} logged out.", ip_address=request.remote_addr)
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    user_logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(20).all()
    return render_template('dashboard.html', profile_view=True, user_logs=user_logs)
