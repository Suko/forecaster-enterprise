from passlib.context import CryptContext

# Password context for hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash with constant-time comparison
    """
    if not hashed_password:
        # Always perform a hash operation to prevent timing attacks
        pwd_context.verify("dummy", "$2b$12$dummy.hash.to.prevent.timing.attacks.abcdefghijklmnopqr")
        return False
    
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password for storing
    """
    return pwd_context.hash(password)

