from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from multiple possible locations
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
        load_dotenv(env_path, override=True)
        _env_loaded = True
        break

# If no .env file found, that's OK - rely on existing environment variables

class Settings(BaseSettings):
    # App settings
    app_name: str = os.getenv("APP_NAME", "Forecaster Enterprise")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]

    # Database URL - PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/forecaster_enterprise"
    )

    # Security - JWT
    secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # CORS Configuration
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")

    def model_post_init(self, __context) -> None:
        """Validate configuration after initialization"""
        # Ensure JWT secret key is set in production
        if not self.secret_key and self.environment.lower() not in ["development", "dev", "local"]:
            raise ValueError("JWT_SECRET_KEY must be set in production environment")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Global settings instance
settings = Settings()

