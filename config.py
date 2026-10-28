import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
    MAX_ROWS = int(os.getenv("MAX_ROWS", 50000))
    MAX_COLUMNS = int(os.getenv("MAX_COLUMNS", 100))
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "datalens")
    BEAUTY_API_BASE = os.getenv("BEAUTY_API_BASE", "https://world.openbeautyfacts.org")
    BEAUTY_API_USER_AGENT = os.getenv("BEAUTY_API_USER_AGENT", "DataLens-Beauty/1.0 (college-project)")
    BEAUTY_API_TIMEOUT = int(os.getenv("BEAUTY_API_TIMEOUT", 10))
