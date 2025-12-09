from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets
import warnings
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

# Load .env file from multiple possible locations
# Use override=False to prevent .env from overwriting runtime environment variables
_backend_dir = Path(__file__).parent
_env_locations = [
    _backend_dir / ".env",  # Primary: backend/.env
    _backend_dir.parent / ".env",  # Fallback: project root .env
    Path.cwd() / ".env",  # Current working directory
]

# Load first available .env file
_env_loaded = False
for env_path in _env_locations:
    if env_path.exists():
        load_dotenv(env_path, override=False)  # Don't override existing env vars
        _env_loaded = True
        break

# If no .env file found, that's OK - rely on existing environment variables

def _generate_dev_secret_key() -> str:
    """Generate a strong secret key for development use only"""
    return secrets.token_urlsafe(32)

def _enforce_database_tls(database_url: str) -> str:
    """
    Enforce TLS for remote database connections.
    Localhost connections are allowed without TLS for development.
    """
    parsed = urlparse(database_url)
    is_localhost = parsed.hostname in ["localhost", "127.0.0.1", "::1"]
    
    if is_localhost:
        return database_url
    
    # For remote databases, enforce TLS
    query_params = parse_qs(parsed.query)
    sslmode = query_params.get("sslmode", [None])[0]
    
    if sslmode not in ["require", "prefer", "verify-ca", "verify-full"]:
        query_params["sslmode"] = ["require"]
        new_query = urlencode(query_params, doseq=True)
        parsed = parsed._replace(query=new_query)
        return urlunparse(parsed)
    
    return database_url

class Settings(BaseSettings):
    # App settings
    app_name: str = os.getenv("APP_NAME", "Forecaster Enterprise")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]

    # Database URL - PostgreSQL (will be processed in model_post_init)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/forecaster_enterprise"
    )

    # Security - JWT (will be processed in model_post_init)
    secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Service API Key - For automated/system forecasts (optional)
    service_api_key: Optional[str] = os.getenv("SERVICE_API_KEY", None)

    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # CORS Configuration
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ["true", "1", "yes"]
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "20"))

    # Data Validation & Audit Logging
    # Enable detailed data validation and audit trail (recommended for testing/development)
    # In production, set to false to reduce overhead (validation still runs, but audit trail is minimal)
    enable_audit_logging: bool = os.getenv("ENABLE_AUDIT_LOGGING", "").lower() in ["true", "1", "yes"] or os.getenv("ENVIRONMENT", "development").lower() in ["development", "dev", "test", "testing"]

    def model_post_init(self, __context) -> None:
        """Validate configuration after initialization"""
        is_dev = self.environment.lower() in ["development", "dev", "local"]
        
        # JWT Secret Key - Required in all environments
        if not self.secret_key:
            if is_dev:
                # Generate a strong dev key but warn
                self.secret_key = _generate_dev_secret_key()
                warnings.warn(
                    "JWT_SECRET_KEY not set. Generated a temporary key for development. "
                    "Set JWT_SECRET_KEY in production!",
                    UserWarning
                )
            else:
                raise ValueError(
                    "JWT_SECRET_KEY must be set in production environment. "
                    "Set the JWT_SECRET_KEY environment variable."
                )
        else:
            if len(self.secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        
        # Database URL - Enforce TLS for remote connections
        self.database_url = _enforce_database_tls(self.database_url)
        
        # Debug mode - Disable in production
        if self.debug and not is_dev:
            raise ValueError(
                "DEBUG mode cannot be enabled in production. "
                "Set ENVIRONMENT=development for debug mode."
            )
        
        # API Host - Restrict binding in production
        if not is_dev and self.api_host == "0.0.0.0":
            warnings.warn(
                "API_HOST=0.0.0.0 is not recommended in production. "
                "Consider binding to 127.0.0.1 and using a reverse proxy.",
                UserWarning
            )
        
        # CORS - Restrict in production
        if not is_dev:
            # In production, require explicit CORS origins (no wildcards)
            if "*" in self.cors_origins or any("localhost" in origin.lower() for origin in self.cors_origins):
                warnings.warn(
                    "CORS_ORIGINS contains localhost or wildcards in production. "
                    "This is not recommended for security.",
                    UserWarning
                )

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Global settings instance
settings = Settings()

