from pwdlib import PasswordHash

# Use pwdlib as recommended by FastAPI
# It uses Argon2 by default (more secure than bcrypt) but can use bcrypt if needed
password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash with constant-time comparison.
    Uses pwdlib (recommended by FastAPI) with Argon2 by default.
    """
    if not hashed_password:
        # Always perform a hash operation to prevent timing attacks
        dummy_hash = password_hash.hash("dummy")
        password_hash.verify("dummy", dummy_hash)
        return False

    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    Uses pwdlib (recommended by FastAPI) with Argon2 by default.
    """
    return password_hash.hash(password)
