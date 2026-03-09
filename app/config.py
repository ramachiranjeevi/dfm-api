import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    # Render provides "postgresql://..." — we normalise to asyncpg at load time.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/DigitalFarming"

    # JWT
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # SMS
    TEXTLOCAL_API_KEY: str = ""
    TEXTLOCAL_SENDER: str = "DFMAGR"

    # Firebase
    FCM_SERVER_KEY: str = ""
    FCM_SENDER_ID: str = ""

    # Web Push (VAPID)
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_EMAIL: str = "mailto:admin@haritham.app"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalise_db_url(cls, v: str) -> str:
        """
        Render (and many cloud providers) give a plain postgresql:// URL.
        SQLAlchemy async engine needs postgresql+asyncpg://.
        This validator ensures the correct driver prefix is always present.
        """
        # Strip any existing driver suffix so we can re-apply cleanly
        v = re.sub(r"^postgresql(\+\w+)?://", "postgresql+asyncpg://", v)
        return v


settings = Settings()
