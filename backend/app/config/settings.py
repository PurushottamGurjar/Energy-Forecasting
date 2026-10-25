from datetime import date
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DELIVERY_START = date(2026, 1, 1)
DELIVERY_END = date(2026, 1, 31)


class Settings(BaseSettings):
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    elexon_timeout_seconds: float = Field(default=30, gt=0)
    forecast_lookback_hours: int = Field(default=72, ge=1, le=24 * 14)
    mape_min_actual_mw: float = Field(default=1.0, ge=0)
    elexon_max_retries: int = Field(default=3, ge=0, le=5)
    default_decision_cutoff_utc: str = "13:00"
    cors_origins: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def elexon_base_url_normalized(self) -> str:
        return self.elexon_base_url.rstrip("/")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
