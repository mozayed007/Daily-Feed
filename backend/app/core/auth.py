import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Set

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token blacklist (use Redis in production)
_token_blacklist: Set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")


def blacklist_token(token: str) -> None:
    """Add a token to the blacklist."""
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        if jti:
            _token_blacklist.add(jti)
    except ValueError:
        pass
    _token_blacklist.add(token)


def create_password_reset_token(email: str) -> str:
    """Create a short-lived password reset token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    data = {"sub": email, "exp": expire, "type": "reset", "jti": str(uuid.uuid4())}
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def is_token_blacklisted(token: str) -> bool:
    """Check if a token has been blacklisted."""
    if token in _token_blacklist:
        return True
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        if jti and jti in _token_blacklist:
            return True
    except ValueError:
        return True
    return False


class TokenData:
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


def create_tokens(user_id: str, email: str) -> dict:
    data = {"sub": user_id, "email": email}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
