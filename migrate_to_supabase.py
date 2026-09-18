"""
Supabase Migration Utility for Land Record Digitization System
Usage:
    python migrate_to_supabase.py "postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres"
Or set DATABASE_URL environment variable and run:
    python migrate_to_supabase.py
"""

import sys
import os
import sqlite3
from datetime import datetime

def migrate(supabase_url=None):
    if not supabase_url:
        supabase_url = os.environ.get("DATABASE_URL")
    
    if not supabase_url:
        print("Error: Please provide your Supabase PostgreSQL connection string.")
        print('Example: python migrate_to_supabase.py "postgresql://postgres.xxx:pass@aws-0-region.pooler.supabase.com:6543/postgres"')
        return False

    if supabase_url.startswith("postgres://"):
        supabase_url = supabase_url.replace("postgres://", "postgresql://", 1)

    os.environ["DATABASE_URL"] = supabase_url

    print("Connecting to Supabase PostgreSQL...")
    from app import create_app
    from models import db, User, LandRecord, Document, Verification, AuditLog

    app = create_app()

    with app.app_context():
        print("Creating all tables in Supabase...")
        db.create_all()
        print("Tables verified / created successfully in Supabase!")

        # Check existing SQLite data
        sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
        if not os.path.exists(sqlite_path):
            print(f"No local database.db found at {sqlite_path}. Seeding default accounts directly...")
            from app import seed_database
            seed_database(app)
            print("Supabase database successfully initialized with demo records!")
            return True

        print(f"Migrating records from local SQLite ({sqlite_path}) into Supabase...")
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. Users
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        for u in users:
            existing = User.query.filter_by(email=u["email"]).first()
            if not existing:
                new_u = User(
                    id=u["id"],
                    email=u["email"],
                    name=u["name"],
                    password_hash=u["password_hash"],
                    role=u["role"],
                    department=u["department"],
                    is_active=bool(u["is_active"]),
                    created_at=datetime.fromisoformat(u["created_at"]) if u["created_at"] else datetime.utcnow()
                )
                db.session.add(new_u)
        db.session.commit()
        print(f"  - Migrated {len(users)} users.")

        # 2. Land Records
        cur.execute("SELECT * FROM land_records")
        records = cur.fetchall()
        for r in records:
            existing = LandRecord.query.filter_by(parcel_id=r["parcel_id"]).first()
            if not existing:
                new_r = LandRecord(
                    id=r["id"],
                    khasra_number=r["khasra_number"],
                    survey_number=r["survey_number"],
                    parcel_id=r["parcel_id"],
                    owner_name=r["owner_name"],
                    co_owners=r["co_owners"],
                    father_or_husband_name=r["father_or_husband_name"],
                    aadhaar_masked=r["aadhaar_masked"],
                    district=r["district"],
                    tehsil=r["tehsil"],
                    village=r["village"],
                    pincode=r["pincode"],
                    land_type=r["land_type"],
                    area_acres=r["area_acres"],
                    area_sqft=r["area_sqft"],
                    market_value=r["market_value"],
                    mutation_number=r["mutation_number"],
                    registration_date=datetime.strptime(r["registration_date"], "%Y-%m-%d").date() if r["registration_date"] else None,
                    north_boundary=r["north_boundary"],
                    south_boundary=r["south_boundary"],
                    east_boundary=r["east_boundary"],
                    west_boundary=r["west_boundary"],
                    status=r["status"],
                    duplicate_risk=r["duplicate_risk"],
                    duplicate_matched_id=r["duplicate_matched_id"],
                    duplicate_notes=r["duplicate_notes"],
                    mismatch_detected=bool(r["mismatch_detected"]),
                    mismatch_notes=r["mismatch_notes"],
                    created_by_id=r["created_by_id"],
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
                )
                db.session.add(new_r)
        db.session.commit()
        print(f"  - Migrated {len(records)} land records.")

        # 3. Documents
        cur.execute("SELECT * FROM documents")
        docs = cur.fetchall()
        for d in docs:
            existing = Document.query.get(d["id"])
            if not existing:
                new_d = Document(
                    id=d["id"],
                    record_id=d["record_id"],
                    filename=d["filename"],
                    original_filename=d["original_filename"],
                    file_path=d["file_path"],
                    file_type=d["file_type"],
                    file_size_kb=d["file_size_kb"],
                    ocr_status=d["ocr_status"],
                    ocr_confidence=d["ocr_confidence"],
                    extracted_text=d["extracted_text"],
                    extracted_json=d["extracted_json"],
                    uploaded_by_id=d["uploaded_by_id"],
                    created_at=datetime.fromisoformat(d["created_at"]) if d["created_at"] else datetime.utcnow()
                )
                db.session.add(new_d)
        db.session.commit()
        print(f"  - Migrated {len(docs)} documents.")

        # 4. Verifications
        cur.execute("SELECT * FROM verifications")
        verifications = cur.fetchall()
        for v in verifications:
            existing = Verification.query.get(v["id"])
            if not existing:
                new_v = Verification(
                    id=v["id"],
                    record_id=v["record_id"],
                    verified_by_id=v["verified_by_id"],
                    status=v["status"],
                    remarks=v["remarks"],
                    title_chain_verified=bool(v["title_chain_verified"]),
                    boundaries_verified=bool(v["boundaries_verified"]),
                    encumbrance_free=bool(v["encumbrance_free"]),
                    ocr_match_verified=bool(v["ocr_match_verified"]),
                    duplicate_checked=bool(v["duplicate_checked"]),
                    verification_date=datetime.fromisoformat(v["verification_date"]) if v["verification_date"] else datetime.utcnow()
                )
                db.session.add(new_v)
        db.session.commit()
        print(f"  - Migrated {len(verifications)} verification records.")

        # 5. Audit Logs
        cur.execute("SELECT * FROM audit_logs")
        logs = cur.fetchall()
        for l in logs:
            existing = AuditLog.query.get(l["id"])
            if not existing:
                new_l = AuditLog(
                    id=l["id"],
                    user_id=l["user_id"],
                    action=l["action"],
                    entity_type=l["entity_type"],
                    entity_id=l["entity_id"],
                    details=l["details"],
                    ip_address=l["ip_address"],
                    timestamp=datetime.fromisoformat(l["timestamp"]) if l["timestamp"] else datetime.utcnow()
                )
                db.session.add(new_l)
        db.session.commit()
        print(f"  - Migrated {len(logs)} audit logs.")

        conn.close()
        print("\nAll data successfully migrated to Supabase PostgreSQL!")
        return True

if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    migrate(url_arg)
