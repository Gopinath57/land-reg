from datetime import datetime
from . import db

class Verification(db.Model):
    __tablename__ = 'verifications'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('land_records.id'), nullable=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.Text, nullable=False)
    
    title_chain_verified = db.Column(db.Boolean, default=False)
    boundaries_verified = db.Column(db.Boolean, default=False)
    encumbrance_free = db.Column(db.Boolean, default=False)
    ocr_match_verified = db.Column(db.Boolean, default=False)
    duplicate_checked = db.Column(db.Boolean, default=False)
    
    verification_date = db.Column(db.DateTime, default=datetime.utcnow)

    def checklist_summary(self):
        checks = [
            ('Title Chain', self.title_chain_verified),
            ('Boundaries', self.boundaries_verified),
            ('Encumbrance Free', self.encumbrance_free),
            ('OCR Match', self.ocr_match_verified),
            ('Duplicate Checked', self.duplicate_checked)
        ]
        passed = sum(1 for _, v in checks if v)
        return f'{passed}/{len(checks)} Verified'
