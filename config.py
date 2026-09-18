import os
import shutil

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IS_VERCEL = os.environ.get('VERCEL') is not None or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

if IS_VERCEL:
    # Vercel serverless environment has a read-only root; only /tmp is writable
    DATA_DIR = '/tmp'
    DB_PATH = os.path.join(DATA_DIR, 'database.db')
    
    # Copy pre-seeded database to /tmp if not already present
    bundled_db = os.path.join(BASE_DIR, 'database.db')
    if os.path.exists(bundled_db) and not os.path.exists(DB_PATH):
        try:
            shutil.copyfile(bundled_db, DB_PATH)
        except Exception:
            pass
            
    UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
    REPORT_DIR = os.path.join(DATA_DIR, 'reports')
else:
    DB_PATH = os.path.join(BASE_DIR, 'database.db')
    UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
    REPORT_DIR = os.path.join(BASE_DIR, 'reports')

# Database URL resolution (Supabase PostgreSQL or fallback SQLite)
raw_db_url = os.environ.get('DATABASE_URL')
if raw_db_url:
    # Supabase gives postgres:// URLs; SQLAlchemy 2.0 requires postgresql://
    if raw_db_url.startswith('postgres://'):
        raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
    DATABASE_URI = raw_db_url
else:
    DATABASE_URI = f"sqlite:///{DB_PATH}"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'land-record-secret-key-2026-auth-secure')
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    } if not DATABASE_URI.startswith('sqlite') else {}
    UPLOAD_FOLDER = UPLOAD_DIR
    REPORT_FOLDER = REPORT_DIR
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tif', 'tiff', 'txt'}
