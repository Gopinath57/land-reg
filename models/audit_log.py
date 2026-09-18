from datetime import datetime
from . import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @staticmethod
    def log(action, user_id=None, entity_type=None, entity_id=None, details=None, ip_address='127.0.0.1'):
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )
        db.session.add(entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
