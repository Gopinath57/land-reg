from .auth import auth_bp
from .dashboard import dashboard_bp
from .records import records_bp
from .documents import documents_bp
from .verification import verification_bp
from .reports import reports_bp
from .admin import admin_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'records_bp',
    'documents_bp',
    'verification_bp',
    'reports_bp',
    'admin_bp'
]
