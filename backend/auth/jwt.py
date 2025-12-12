from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import settings

# Constants for better maintainability
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    """
    Create a new access token with expiration
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str, expected_type: str = "access"):
    """
    Decode and validate JWT token with type checking

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        # Validate token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise JWTError(f"Invalid token type. Expected '{expected_type}', got '{token_type}'")

        return payload
    except JWTError as e:
        raise e


