from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    app_name: str = "Employ Research API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://employ_research:change-me-in-local-env@postgres:5432/employ_research"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret_key: str = Field(min_length=32)
    jwt_access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    user_secrets_encryption_key: str
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""
    backend_cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.backend_cors_origins.split(",") if value.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
