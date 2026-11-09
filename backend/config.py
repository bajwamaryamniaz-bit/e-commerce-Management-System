import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ecommerce-super-secret-key-change-in-production")
    
    # Database Configuration
    # Supports both discrete params and full DATABASE_URL (for cloud hosting like Neon)
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "ecommerce_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    
    # Engine mode: postgresql (default as per project requirements) or sqlite (offline fallback)
    DB_ENGINE = os.getenv("DB_ENGINE", "postgresql").lower()
    
    # SQLite Path: On Vercel serverless environment, filesystem is read-only except /tmp
    _base_sqlite = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")
    if os.getenv("VERCEL"):
        _tmp_sqlite = "/tmp/ecommerce.db"
        if not os.path.exists(_tmp_sqlite) and os.path.exists(_base_sqlite):
            import shutil
            try:
                shutil.copyfile(_base_sqlite, _tmp_sqlite)
            except Exception:
                pass
        SQLITE_PATH = _tmp_sqlite if os.path.exists(_tmp_sqlite) else _base_sqlite
    else:
        SQLITE_PATH = _base_sqlite
