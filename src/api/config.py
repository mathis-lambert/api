from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    maintenance_mode: bool = False

    secret_key: str | None = None

    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_username: str = "root"
    mongodb_password: str = "example"
    mongodb_database: str = "api-database"

    qdrant_api_key: str | None = None
    qdrant_url: str | None = None

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str | None = None
    openrouter_app_name: str | None = None

    openai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
