import json
from datetime import datetime
from . import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('land_records.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False, default='Sale Deed')
    file_size_kb = db.Column(db.Float, default=0.0)
    
    ocr_status = db.Column(db.String(30), default='Pending')
    ocr_confidence = db.Column(db.Float, default=0.0)
    extracted_text = db.Column(db.Text, nullable=True)
    extracted_json = db.Column(db.Text, nullable=True)
    
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def parsed_data(self):
        if self.extracted_json:
            try:
                return json.loads(self.extracted_json)
            except Exception:
                return {}
        return {}

    def set_parsed_data(self, data_dict):
        self.extracted_json = json.dumps(data_dict, indent=2)
