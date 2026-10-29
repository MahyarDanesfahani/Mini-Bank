from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "صندوق من"
    database_url: str = "sqlite:///./data/fund.db"
    jwt_secret: str = "development-only-change-me"
    jwt_expire_minutes: int = 60
    owner_setup_key: str = "change-this-setup-key"
    api_prefix: str = "/api/v1"
    app_environment: str = "development"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def validate_production_settings() -> None:
    """Fail closed when a production deployment still uses development secrets."""
    if settings.app_environment.lower() != "production":
        return
    unsafe = {"development-only-change-me", "change-this-setup-key"}
    if settings.jwt_secret in unsafe or len(settings.jwt_secret) < 32:
        raise RuntimeError("Set JWT_SECRET to a unique random value of at least 32 characters in production.")
    if settings.owner_setup_key in unsafe or len(settings.owner_setup_key) < 24:
        raise RuntimeError("Set OWNER_SETUP_KEY to a unique random value of at least 24 characters in production.")
    if not settings.cors_origins or "*" in settings.cors_origins:
        raise RuntimeError("Set CORS_ORIGINS to the exact public app origin(s) in production.")
