import bcrypt
from typing import Optional

# Use bcrypt directly to avoid passlib initialization issues
# This is more reliable and has better compatibility


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash with constant-time comparison.
    Uses bcrypt directly for better compatibility.
    """
    if not hashed_password:
        # Always perform a hash operation to prevent timing attacks
        dummy_hash = bcrypt.hashpw(b"dummy", bcrypt.gensalt())
        bcrypt.checkpw(b"dummy", dummy_hash)
        return False
    
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    Uses bcrypt directly for better compatibility.
    """
    # Ensure password is not longer than 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
