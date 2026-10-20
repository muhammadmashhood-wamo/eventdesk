from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App info (safe defaults)
    PROJECT_NAME: str = "EventDeskApi"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Credentials & Secrets (Required: strictly loaded from .env)
    DATABASE_URL: str
    SECRET_KEY: str

    # JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
