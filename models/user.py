from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Revenue Officer')
    department = db.Column(db.String(100), default='Revenue & Land Records Dept')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_records = db.relationship('LandRecord', backref='creator', lazy=True, foreign_keys='LandRecord.created_by_id')
    uploaded_docs = db.relationship('Document', backref='uploader', lazy=True, foreign_keys='Document.uploaded_by_id')
    verifications = db.relationship('Verification', backref='verifier', lazy=True, foreign_keys='Verification.verified_by_id')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, foreign_keys='AuditLog.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'Administrator'

    @property
    def is_revenue_officer(self):
        return self.role in ['Revenue Officer', 'Administrator']

    @property
    def is_verification_officer(self):
        return self.role in ['Verification Officer', 'Administrator']

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
