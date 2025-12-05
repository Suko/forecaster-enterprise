from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import settings

# Constants for better maintainability
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict):
    """
    Create a new access token with expiration
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(data: dict):
    """
    Create a new refresh token with expiration
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str):
    """
    Decode and validate JWT token
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        raise e

def is_token_valid(token: str):
    """
    Check if a token is valid (not expired)
    """
    try:
        payload = decode_token(token)
        expiration = datetime.fromtimestamp(payload.get("exp"))
        return datetime.utcnow() < expiration
    except JWTError:
        return False

