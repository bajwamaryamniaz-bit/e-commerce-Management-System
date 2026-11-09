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
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")
