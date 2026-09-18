from datetime import datetime
from . import db

class LandRecord(db.Model):
    __tablename__ = 'land_records'

    id = db.Column(db.Integer, primary_key=True)
    khasra_number = db.Column(db.String(64), nullable=False, index=True)
    survey_number = db.Column(db.String(64), nullable=False, index=True)
    parcel_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    owner_name = db.Column(db.String(150), nullable=False, index=True)
    co_owners = db.Column(db.String(300), nullable=True)
    father_or_husband_name = db.Column(db.String(150), nullable=True)
    aadhaar_masked = db.Column(db.String(20), nullable=True)
    
    district = db.Column(db.String(100), nullable=False, index=True)
    tehsil = db.Column(db.String(100), nullable=False)
    village = db.Column(db.String(100), nullable=False, index=True)
    pincode = db.Column(db.String(10), nullable=True)
    
    land_type = db.Column(db.String(50), nullable=False, default='Agricultural')
    area_acres = db.Column(db.Float, nullable=False, default=0.0)
    area_sqft = db.Column(db.Float, nullable=True, default=0.0)
    market_value = db.Column(db.Float, nullable=False, default=0.0)
    mutation_number = db.Column(db.String(64), nullable=True)
    registration_date = db.Column(db.Date, nullable=True)
    
    north_boundary = db.Column(db.String(200), nullable=True)
    south_boundary = db.Column(db.String(200), nullable=True)
    east_boundary = db.Column(db.String(200), nullable=True)
    west_boundary = db.Column(db.String(200), nullable=True)

    status = db.Column(db.String(50), default='Pending Verification', index=True)
    
    duplicate_risk = db.Column(db.String(20), default='None')
    duplicate_matched_id = db.Column(db.Integer, nullable=True)
    duplicate_notes = db.Column(db.Text, nullable=True)
    mismatch_detected = db.Column(db.Boolean, default=False)
    mismatch_notes = db.Column(db.Text, nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = db.relationship('Document', backref='record', lazy=True, cascade='all, delete-orphan')
    verifications = db.relationship('Verification', backref='record', lazy=True, cascade='all, delete-orphan', order_by='desc(Verification.verification_date)')

    def calculate_sqft(self):
        if self.area_acres:
            self.area_sqft = round(self.area_acres * 43560, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'khasra_number': self.khasra_number,
            'survey_number': self.survey_number,
            'parcel_id': self.parcel_id,
            'owner_name': self.owner_name,
            'co_owners': self.co_owners,
            'father_or_husband_name': self.father_or_husband_name,
            'district': self.district,
            'tehsil': self.tehsil,
            'village': self.village,
            'land_type': self.land_type,
            'area_acres': self.area_acres,
            'area_sqft': self.area_sqft,
            'market_value': self.market_value,
            'status': self.status,
            'duplicate_risk': self.duplicate_risk,
            'duplicate_notes': self.duplicate_notes,
            'mismatch_detected': self.mismatch_detected,
            'mismatch_notes': self.mismatch_notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }
