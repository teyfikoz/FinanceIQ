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
    PROJECT_NAME: str = "FundPilot"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    APP_DISPLAY_NAME: str = "FundPilot"
    PUBLIC_SITE_URL: str = os.environ.get("PUBLIC_SITE_URL", "https://fundpilot.techsyncanalytica.com")
    SUPPORT_EMAIL: str = os.environ.get("SUPPORT_EMAIL", "techsyncanalytica@gmail.com")

    # Security - MUST be set via environment variable in production
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "password")
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
    FRED_API_KEY: Optional[str] = os.environ.get("FRED_API_KEY")
    TCMB_EVDS_API_KEY: Optional[str] = os.environ.get("TCMB_EVDS_API_KEY")
    TCMB_EVDS_BASE_URL: str = os.environ.get(
        "TCMB_EVDS_BASE_URL",
        "https://evds3.tcmb.gov.tr/igmevdsms-dis",
    )
    COINGECKO_API_KEY: Optional[str] = os.environ.get("COINGECKO_API_KEY")
    ALTERNATIVE_ME_API_KEY: Optional[str] = os.environ.get("ALTERNATIVE_ME_API_KEY")
    TREASURY_FISCALDATA_BASE_URL: str = os.environ.get(
        "TREASURY_FISCALDATA_BASE_URL",
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service",
    )
    ENABLE_STOOQ_FALLBACK: bool = True

    # Rate Limiting
    API_RATE_LIMIT: int = 100
    COINGECKO_RATE_LIMIT: int = 50

    # Environment
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    DEBUG: bool = os.environ.get("DEBUG", "").lower() in {"1", "true", "yes"} if os.environ.get("DEBUG") else ENVIRONMENT != "production"
    ENABLE_API_DOCS: bool = os.environ.get("ENABLE_API_DOCS", "").lower() in {"1", "true", "yes"} if os.environ.get("ENABLE_API_DOCS") else ENVIRONMENT != "production"
    ENABLE_PREWARM_WORKER: bool = os.environ.get("ENABLE_PREWARM_WORKER", "").lower() in {"1", "true", "yes"} if os.environ.get("ENABLE_PREWARM_WORKER") else ENVIRONMENT == "production"
    PREWARM_INTERVAL_SECONDS: int = int(os.environ.get("PREWARM_INTERVAL_SECONDS", "900"))
    PUBLIC_SNAPSHOT_DIR: str = os.environ.get("PUBLIC_SNAPSHOT_DIR", "data/public_snapshots")
    PUBLIC_TR_FUNDS_MONTHS: int = int(os.environ.get("PUBLIC_TR_FUNDS_MONTHS", "3"))
    PUBLIC_RESEARCH_TTL_SECONDS: int = int(os.environ.get("PUBLIC_RESEARCH_TTL_SECONDS", "1800"))
    PUBLIC_DEFAULT_STOCK_SYMBOL: str = os.environ.get("PUBLIC_DEFAULT_STOCK_SYMBOL", "AAPL")
    PUBLIC_DEFAULT_FUND_SYMBOL: str = os.environ.get("PUBLIC_DEFAULT_FUND_SYMBOL", "SPY")
    PUBLIC_DEFAULT_FORECAST_SYMBOL: str = os.environ.get("PUBLIC_DEFAULT_FORECAST_SYMBOL", "NVDA")
    PUBLIC_DEFAULT_FORECAST_DAYS: int = int(os.environ.get("PUBLIC_DEFAULT_FORECAST_DAYS", "30"))
    PUBLIC_DEFAULT_TR_FUND_CODE: str = os.environ.get("PUBLIC_DEFAULT_TR_FUND_CODE", "TCD")
    PUBLIC_DEFAULT_OWNERSHIP_SYMBOL: str = os.environ.get("PUBLIC_DEFAULT_OWNERSHIP_SYMBOL", "AAPL")
    PUBLIC_DEFAULT_OWNERSHIP_FOCUS: str = os.environ.get("PUBLIC_DEFAULT_OWNERSHIP_FOCUS", "core")
    PUBLIC_DEFAULT_SCREENER_UNIVERSE: str = os.environ.get("PUBLIC_DEFAULT_SCREENER_UNIVERSE", "sp500")
    PUBLIC_DEFAULT_SCREENER_SCREEN: str = os.environ.get("PUBLIC_DEFAULT_SCREENER_SCREEN", "momentum_stocks")
    PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER: str = os.environ.get("PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER", "berkshire")
    PUBLIC_SEC_USER_AGENT: str = os.environ.get(
        "PUBLIC_SEC_USER_AGENT",
        f"FundPilot/2.0 ({os.environ.get('SUPPORT_EMAIL', 'techsyncanalytica@gmail.com')})",
    )
    LOG_LEVEL: str = "INFO"

    # CORS - Using List[str] instead of List[AnyHttpUrl] to avoid validation errors
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
        "https://fundpilot.techsyncanalytica.com",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        # Handle empty or None values
        if not v or v == "":
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://localhost:8501",
                "https://fundpilot.techsyncanalytica.com",
            ]

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
                return [v] if v else [
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://localhost:8501",
                    "https://fundpilot.techsyncanalytica.com",
                ]
        return [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8501",
            "https://fundpilot.techsyncanalytica.com",
        ]

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
