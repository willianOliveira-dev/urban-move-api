from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "UrbanMove API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = Field(...)

    SUPABASE_URL: str = Field(...)
    SUPABASE_ANON_KEY: str = Field(...)

    REDIS_URL: str = "redis://localhost:6379/0"

    SPTRANS_API_URL: str = "https://api.olhovivo.sptrans.com.br/v2.1"
    SPTRANS_API_TOKEN: str = Field(...)

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    GOOGLE_MAPS_API_KEY: str = Field(...)

    LOG_LEVEL: str = "INFO"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.SUPABASE_URL}/auth/v1/.well-known/jwks.json"


env = Env()
