from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .land_record import LandRecord
from .document import Document
from .verification import Verification
from .audit_log import AuditLog

__all__ = ['db', 'User', 'LandRecord', 'Document', 'Verification', 'AuditLog']
