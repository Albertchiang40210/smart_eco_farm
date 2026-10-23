import hmac
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login", auto_error=False)

# 管理員帳號來自環境變數；啟動時只雜湊一次。未設定密碼 = 停用登入。
_admin_hash = pwd_context.hash(settings.ADMIN_PASSWORD) if settings.ADMIN_PASSWORD else None


def authenticate_admin(username: str, password: str) -> bool:
    if _admin_hash is None:
        return False
    # 無論帳號是否正確都做一次雜湊比對，避免從回應時間推測帳號
    ok = pwd_context.verify(password, _admin_hash)
    return ok and hmac.compare_digest(username, settings.ADMIN_USERNAME)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def _decode_user(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
    except JWTError:
        return None


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> str:
    username = _decode_user(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


def _valid_device_key(key: str | None) -> bool:
    return bool(settings.DEVICE_API_KEY and key and hmac.compare_digest(key, settings.DEVICE_API_KEY))


def require_device(x_api_key: str | None = Header(default=None)) -> str:
    """IoT 感測器專用：以 X-API-Key 驗證。"""
    if not _valid_device_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return "device"


def require_user_or_device(
    token: str | None = Depends(oauth2_scheme),
    x_api_key: str | None = Header(default=None),
) -> str:
    """影像診斷 API：登入使用者(JWT)或手機巡檢端(API Key)皆可。"""
    user = _decode_user(token)
    if user:
        return user
    if _valid_device_key(x_api_key):
        return "device"
    raise HTTPException(status_code=401, detail="Authentication required")
