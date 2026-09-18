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

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'land-record-secret-key-2026-auth-secure')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_DIR
    REPORT_FOLDER = REPORT_DIR
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tif', 'tiff', 'txt'}
