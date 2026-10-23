"""集中管理環境變數。敏感值一律來自 .env / 環境變數，不寫死在程式碼。"""
import os
import secrets

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_eco_farm_db")
# 測試時可直接指定 sqlite:///... 覆蓋
DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}?charset=utf8mb4"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("未設定 SECRET_KEY，已產生臨時金鑰（重啟後所有 token 失效）")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 8 * 1024 * 1024))
SKIP_MODEL_LOAD = os.getenv("SKIP_MODEL_LOAD", "0") == "1"
