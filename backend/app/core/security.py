from datetime import UTC, datetime, timedelta
import jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, digest: str) -> bool:
    return password_hash.verify(password, digest)

def create_access_token(subject: str) -> tuple[str, int]:
    delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = jwt.encode({"sub": subject, "exp": datetime.now(UTC) + delta}, settings.jwt_secret_key, algorithm="HS256")
    return token, int(delta.total_seconds())

