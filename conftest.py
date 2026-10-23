"""測試環境：SQLite + 不載入 YOLO 模型，不需要 MySQL / Redis。"""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ.update(
    DATABASE_URL=f"sqlite:///{_tmp}/test.db",
    SECRET_KEY="test-secret",
    ADMIN_USERNAME="admin",
    ADMIN_PASSWORD="test-pass",
    DEVICE_API_KEY="test-device-key",
    SKIP_MODEL_LOAD="1",
    REDIS_HOST="127.0.0.1",
)
