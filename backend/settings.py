from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://sme:sme@localhost:5432/sme_finance"
    STORAGE_DIR: str = "storage"
    CORS_ORIGINS: str = "*"

    def cors_list(self) -> list[str]:
        s = (self.CORS_ORIGINS or "").strip()
        if s == "*" or s == "":
            return ["*"]
        return [x.strip() for x in s.split(",") if x.strip()]


settings = Settings()
