from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BASE_DIR / ".env"

load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    S3_BUCKET_NAME: str | None = None
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_REGION: str | None = None
    S3_PUBLIC_BASE_URL: str | None = None
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    GMAIL_CREDENTIALS_FILE: str | None = None
    GMAIL_TOKEN_FILE: str | None = None
    GMAIL_SENDER: str | None = None
    WHATSAPP_ACCESS_TOKEN: str | None = None
    WHATSAPP_PHONE_NUMBER_ID: str | None = None
    WHATSAPP_API_VERSION: str = "v23.0"
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: int = 10
    RATE_LIMIT_REGISTER: int = 5
    RATE_LIMIT_TRACK_ORDER: int = 30
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")


@lru_cache()
def get_settings():
    return Settings()
