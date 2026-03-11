import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings."""

    # Default to sqlite, but can be overridden with environment variables
    DATABASE_PROVIDER: str = "sqlite"  # Options: "sqlite", "postgres"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/open_advocacy.db"

    # Database connection pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # TODO: Change this
    # Default admin user (for development only)
    ADMIN_USERNAME: str = "admin"

    ENVIRONMENT: str = "development"

    # TODO: Tweak this if geocoding with different providers is properly implemented
    GEOCODING_SERVICE: str | None = None  # "google", "mapbox", etc.
    GEOCODING_API_KEY: str | None = None

    ALLOWED_ORIGIN: str | None = None

    OPENSTATES_API_KEY: str | None = None

    DATA_DIR: str | None = None

    AUTH_SECRET_KEY: str | None = None

    SEED_LOCATIONS: str = ""  # Comma-separated, e.g. "chicago" or "chicago,illinois"
    SEED_PROJECTS: str = ""  # Comma-separated, e.g. "adu" or "adu,example"

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"


settings = Settings()
