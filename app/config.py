from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    TELEGRAM_TOKEN: str
    CHANNEL_ID: str
    MESSAGE_THREAD_ID: int | None = 719

    SCAN_INTERVAL_MINUTES: int = 1
    STARTUP_SCAN: bool = True

    DATABASE_PATH: str = "/app/data/offers.db"
    LOG_LEVEL: str = "INFO"

    HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    MAX_OFFERS_PER_SOURCE: int = 10

    REQUEST_DELAY_MS: int = 700
    RANDOM_DELAY_MIN_MS: int = 500
    RANDOM_DELAY_MAX_MS: int = 1600

    USER_AGENT: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    ONLY_MODELS: str = ""
    EXCLUDED_KEYWORDS: str = (
        "pad,kontroler,controller,gamepad,joycon,joy-con,dualshock,dualsense,"
        "kierownica,pedały,pedaly,thrustmaster,logitech g29,g920,g923,fanatec,"
        "gra,gry,game,games,cd,key,klucz,konto,"
        "etui,case,pokrowiec,obudowa,stojak,stand,dock,stacja dokująca,stacja dokujaca,"
        "ładowarka,ladowarka,kabel,zasilacz,uchwyt,adapter,"
        "pudełko,pudelko,karton,box,samo pudełko,samo pudelko,"
        "na części,na czesci,części,czesci,uszkodzony,uszkodzona,"
        "tv,telewizor,monitor,projektor,"
        "ps1,ps2,ps3,ps4,playstation 1,playstation 2,playstation 3,playstation 4,"
        "xbox one,xbox 360,switch lite"
    )

    PREFERRED_LOCATIONS: str = ""
    PREFERRED_REGIONS: str = ""

    MIN_DEAL_SCORE: float = 0.00
    MIN_PRICE: float = 300
    MAX_PRICE: float = 10000
    MAX_PRICE_BY_MODEL_JSON: str = (
        '{"xbox series s": 1800, "xbox series x": 2800, '
        '"playstation 5": 3200, "playstation portal": 1400, '
        '"nintendo switch": 1600, "nintendo switch 2": 3500, '
        '"steam deck": 3200}'
    )

    ENABLE_VINTED: bool = True
    ENABLE_OLX: bool = True
    ENABLE_ALLEGRO_LOKALNIE: bool = True

    ENABLE_TRANSLATION: bool = True
    TRANSLATE_TO_LANGUAGE: str = "pl"

    ENABLE_MARKET_BASELINE_REFRESH: bool = True
    BASELINE_REFRESH_INTERVAL_HOURS: int = 24
    BASELINE_MAX_OFFERS_PER_QUERY: int = 60
    BASELINE_MIN_SAMPLES_FOR_STORAGE: int = 4
    BASELINE_MIN_SAMPLES_FOR_MODEL: int = 6

    @field_validator("SCAN_INTERVAL_MINUTES")
    @classmethod
    def validate_scan_interval(cls, value: int) -> int:
        if value < 1:
            raise ValueError("SCAN_INTERVAL_MINUTES musi być >= 1")
        return value

    @field_validator("RANDOM_DELAY_MAX_MS")
    @classmethod
    def validate_random_delay_max(cls, value: int) -> int:
        if value < 0:
            raise ValueError("RANDOM_DELAY_MAX_MS musi być >= 0")
        return value

    @field_validator("RANDOM_DELAY_MIN_MS")
    @classmethod
    def validate_random_delay_min(cls, value: int) -> int:
        if value < 0:
            raise ValueError("RANDOM_DELAY_MIN_MS musi być >= 0")
        return value

    @property
    def only_models_list(self) -> List[str]:
        return [x.strip().lower() for x in self.ONLY_MODELS.split(",") if x.strip()]

    @property
    def excluded_keywords_list(self) -> List[str]:
        return [x.strip().lower() for x in self.EXCLUDED_KEYWORDS.split(",") if x.strip()]

    @property
    def preferred_locations_list(self) -> List[str]:
        return [x.strip().lower() for x in self.PREFERRED_LOCATIONS.split(",") if x.strip()]

    @property
    def preferred_regions_list(self) -> List[str]:
        return [x.strip().lower() for x in self.PREFERRED_REGIONS.split(",") if x.strip()]

    @property
    def max_price_by_model(self) -> Dict[str, float]:
        try:
            data = json.loads(self.MAX_PRICE_BY_MODEL_JSON or "{}")
            return {str(k).lower(): float(v) for k, v in data.items()}
        except Exception:
            return {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
