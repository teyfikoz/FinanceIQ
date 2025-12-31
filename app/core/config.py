from typing import Any, Dict, List, Optional, Union
import os

from pydantic import PostgresDsn, field_validator

try:
    from pydantic_settings import BaseSettings
except Exception:
    class BaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Global Liquidity Dashboard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "your-super-secret-jwt-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "liquidity_dashboard"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> Any:
        if isinstance(v, str):
            return v
        # Use environment variables directly since values dict is not available in Pydantic v2
        return PostgresDsn.build(
            scheme="postgresql",
            username=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            host=os.getenv("POSTGRES_SERVER", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            path=f"/{os.getenv('POSTGRES_DB', 'liquidity_dashboard')}",
        )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Keys
    FRED_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    ALTERNATIVE_ME_API_KEY: Optional[str] = None
    ENABLE_STOOQ_FALLBACK: bool = True

    # Rate Limiting
    API_RATE_LIMIT: int = 100
    COINGECKO_RATE_LIMIT: int = 50

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # CORS - Using List[str] instead of List[AnyHttpUrl] to avoid validation errors
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        # Handle empty or None values
        if not v or v == "":
            return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8501"]

        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            # Handle JSON string format
            import json
            try:
                return json.loads(v)
            except:
                return [v] if v else ["http://localhost:3000", "http://localhost:8000", "http://localhost:8501"]
        return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8501"]

    # Data Configuration
    UPDATE_FREQUENCY_HOURS: int = 24
    DATA_RETENTION_DAYS: int = 730
    BACKUP_FREQUENCY_DAYS: int = 1

    # Streamlit
    STREAMLIT_PORT: int = 8501
    API_PORT: int = 8000

    # Alerts
    ENABLE_ALERTS: bool = True
    ALERT_EMAIL: Optional[str] = None
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Correlation thresholds
    CORRELATION_ALERT_THRESHOLD: float = 0.2
    VOLATILITY_ALERT_THRESHOLD: float = 25.0
    LIQUIDITY_ALERT_THRESHOLD: float = 2.0

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Don't fail on validation errors
        validate_assignment = False


# Safe initialization with fallback
try:
    settings = Settings()
except Exception as e:
    print(f"⚠️ Warning: Could not load settings from .env: {e}")
    print("Using default settings without .env file...")
    # Create settings WITHOUT reading .env file
    class SafeSettings(Settings):
        class Config:
            env_file = None  # Don't read .env
            case_sensitive = True
    settings = SafeSettings()