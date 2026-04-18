# Console Flipper Bot — pełny kod projektu

## `.env.example`

```python
TELEGRAM_TOKEN=123456:ABCDEF
CHANNEL_ID=@twoj_kanal_lub_-1001234567890

SCAN_INTERVAL_MINUTES=5
STARTUP_SCAN=true

DATABASE_PATH=/app/data/offers.db
LOG_LEVEL=INFO

HEADLESS=true
PLAYWRIGHT_TIMEOUT_MS=30000
MAX_OFFERS_PER_SOURCE=18
REQUEST_DELAY_MS=900
RANDOM_DELAY_MIN_MS=500
RANDOM_DELAY_MAX_MS=1800
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36

ONLY_MODELS=
EXCLUDED_KEYWORDS=konto,pudełko,samo pudełko,pudelko,etui,case,pokrowiec,gra,gry,pad,pady,controller,kontroler,kontrolery,joy-con,joy con,dock,stacja dokująca,stacja dokujaca,ładowarka,ladowarka,zasilacz,kabel,obudowa,na części,na czesci,uszkodzona,uszkodzony
PREFERRED_LOCATIONS=
PREFERRED_REGIONS=

MIN_DEAL_SCORE=0.03
MIN_PRICE=300
MAX_PRICE=5000
MAX_PRICE_BY_MODEL_JSON={"xbox series s": 1800, "xbox series x": 2600, "nintendo switch": 1700, "nintendo switch 2": 3200, "playstation 5": 3000, "steam deck": 3200}

ENABLE_VINTED=true
ENABLE_OLX=true
ENABLE_ALLEGRO_LOKALNIE=true

ENABLE_TRANSLATION=true
TRANSLATE_TO_LANGUAGE=pl

ENABLE_MARKET_BASELINE_REFRESH=true
BASELINE_REFRESH_INTERVAL_HOURS=12
BASELINE_MAX_OFFERS_PER_QUERY=60
BASELINE_MIN_SAMPLES_FOR_STORAGE=4
BASELINE_MIN_SAMPLES_FOR_MODEL=6

CONCURRENT_DETAIL_PAGES=4

```

## `Dockerfile`

```python
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends     ca-certificates     fonts-liberation     libasound2     libatk-bridge2.0-0     libatk1.0-0     libcups2     libdbus-1-3     libdrm2     libgbm1     libglib2.0-0     libgtk-3-0     libnspr4     libnss3     libx11-6     libx11-xcb1     libxcb1     libxcomposite1     libxdamage1     libxext6     libxfixes3     libxkbcommon0     libxrandr2     wget     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

RUN mkdir -p /app/data

CMD ["python", "-m", "app.main"]

```

## `README.md`

```python
# Console Flipper Bot

Telegram bot do wyszukiwania okazji na konsole z:
- Allegro Lokalnie
- OLX
- Vinted

Monitorowane konsole:
- Xbox Series X
- Xbox Series S
- Nintendo Switch
- Nintendo Switch 2
- PlayStation 5
- Steam Deck

## Funkcje
- async scraping przez Playwright
- scheduler przez APScheduler
- deduplikacja ofert w SQLite
- liczenie median cen i score okazji
- filtrowanie akcesoriów, gier, pudełek i części
- publikacja na Telegram z miniaturką, ceną i linkiem
- konfiguracja przez `.env`
- gotowy Dockerfile i Railway config

## Uruchomienie lokalne

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
python -m app.main
```

## Komendy Telegram
- `/start`
- `/health`
- `/scan_now`

## Uwagi
Selektory DOM na marketplace'ach potrafią się zmieniać, więc po wdrożeniu warto zrobić test live i ewentualnie podstroić scrapery.

```

## `app/__init__.py`

```python

```

## `app/bot_handlers.py`

```python
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import Database
from app.services.flipper_service import FlipperService


def setup_handlers(db: Database, flipper: FlipperService) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        await message.answer(
            "Cześć. Jestem Console Flipper Bot.\n"
            "Skanuję OLX, Vinted i Allegro Lokalnie i publikuję okazje na konsole."
        )

    @router.message(Command("health"))
    async def cmd_health(message: Message) -> None:
        seen_count = await db.count_seen()
        await message.answer(
            "✅ Bot działa\n"
            f"📦 Zapisane ogłoszenia seen: {seen_count}"
        )

    @router.message(Command("scan_now"))
    async def cmd_scan_now(message: Message) -> None:
        if flipper._scan_lock.locked():
            await message.answer("⏳ Skan już trwa. Poczekaj aż się skończy.")
            return

        await message.answer("🔎 Uruchamiam ręczny skan...")
        await flipper.run_scan()
        await message.answer("✅ Ręczny skan zakończony.")

    return router

```

## `app/config.py`

```python
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

    SCAN_INTERVAL_MINUTES: int = 5
    STARTUP_SCAN: bool = True

    DATABASE_PATH: str = "/app/data/offers.db"
    LOG_LEVEL: str = "INFO"

    HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    MAX_OFFERS_PER_SOURCE: int = 18
    REQUEST_DELAY_MS: int = 900
    RANDOM_DELAY_MIN_MS: int = 500
    RANDOM_DELAY_MAX_MS: int = 1800
    USER_AGENT: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    ONLY_MODELS: str = ""
    EXCLUDED_KEYWORDS: str = (
        "konto,pudełko,samo pudełko,pudelko,etui,case,pokrowiec,gra,gry,pad,pady,controller,"
        "kontroler,kontrolery,joy-con,joy con,dock,stacja dokująca,stacja dokujaca,ładowarka,"
        "ladowarka,zasilacz,kabel,obudowa,na części,na czesci,uszkodzona,uszkodzony"
    )
    PREFERRED_LOCATIONS: str = ""
    PREFERRED_REGIONS: str = ""

    MIN_DEAL_SCORE: float = 0.03
    MIN_PRICE: float = 300
    MAX_PRICE: float = 5000
    MAX_PRICE_BY_MODEL_JSON: str = '{"xbox series s": 1800, "xbox series x": 2600, "nintendo switch": 1700, "nintendo switch 2": 3200, "playstation 5": 3000, "steam deck": 3200}'

    ENABLE_VINTED: bool = True
    ENABLE_OLX: bool = True
    ENABLE_ALLEGRO_LOKALNIE: bool = True

    ENABLE_TRANSLATION: bool = True
    TRANSLATE_TO_LANGUAGE: str = "pl"

    ENABLE_MARKET_BASELINE_REFRESH: bool = True
    BASELINE_REFRESH_INTERVAL_HOURS: int = 12
    BASELINE_MAX_OFFERS_PER_QUERY: int = 60
    BASELINE_MIN_SAMPLES_FOR_STORAGE: int = 4
    BASELINE_MIN_SAMPLES_FOR_MODEL: int = 6

    CONCURRENT_DETAIL_PAGES: int = 4

    @field_validator("SCAN_INTERVAL_MINUTES")
    @classmethod
    def validate_scan_interval(cls, value: int) -> int:
        if value < 1:
            raise ValueError("SCAN_INTERVAL_MINUTES musi być >= 1")
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

```

## `app/constants.py`

```python
CONSOLE_MODELS = [
    "xbox series x",
    "xbox series s",
    "nintendo switch 2",
    "nintendo switch",
    "playstation 5",
    "steam deck",
]

MODEL_ALIASES = {
    "xbox series x": [
        "xbox series x",
        "xsx",
    ],
    "xbox series s": [
        "xbox series s",
        "xss",
        "x box series s",
    ],
    "nintendo switch 2": [
        "nintendo switch 2",
        "switch 2",
    ],
    "nintendo switch": [
        "nintendo switch",
        "switch oled",
        "switch v1",
        "switch v2",
        "switch hac",
    ],
    "playstation 5": [
        "playstation 5",
        "play station 5",
        "ps5",
    ],
    "steam deck": [
        "steam deck",
        "steamdeck",
    ],
}

STORAGE_PATTERNS = [
    "64gb", "128gb", "256gb", "512gb", "1tb",
]

COLOR_KEYWORDS = [
    "black", "white", "blue", "red", "gray", "grey", "silver",
    "czarny", "biały", "bialy", "niebieski", "czerwony", "szary", "srebrny",
]

CONDITION_KEYWORDS = {
    "jak nowa": ["jak nowa", "stan idealny", "idealny", "perfekcyjny", "bardzo zadbana"],
    "bardzo dobry": ["bardzo dobry", "super stan", "ładny stan", "ladny stan", "db+"],
    "dobry": ["dobry", "sprawna", "sprawny", "używana", "uzywana"],
    "uszkodzona": ["uszkodzona", "na części", "na czesci", "nie działa", "nie dziala"],
}

PLATFORM_NAMES = {
    "vinted": "Vinted",
    "olx": "OLX",
    "allegro_lokalnie": "Allegro Lokalnie",
}

SEARCH_TARGETS = {
    "allegro_lokalnie": {
        "xbox series x": "https://allegrolokalnie.pl/oferty/q/xbox%20series%20x?sort=startingTime-desc",
        "xbox series s": "https://allegrolokalnie.pl/oferty/q/xbox%20series%20s?sort=startingTime-desc",
        "nintendo switch": "https://allegrolokalnie.pl/oferty/q/nintendo%20switch?sort=startingTime-desc",
        "nintendo switch 2": "https://allegrolokalnie.pl/oferty/q/nintendo%20switch%202?sort=startingTime-desc",
        "playstation 5": "https://allegrolokalnie.pl/oferty/q/playstation%205?sort=startingTime-desc",
        "steam deck": "https://allegrolokalnie.pl/oferty/q/steam%20deck?sort=startingTime-desc",
    },
    "olx": {
        "xbox series s": "https://www.olx.pl/oferty/q-xbox-series-s/?search%5Border%5D=created_at:desc",
        "xbox series x": "https://www.olx.pl/oferty/q-xbox-series-x/?search%5Border%5D=created_at:desc",
        "nintendo switch": "https://www.olx.pl/oferty/q-nintendo-switch/?search%5Border%5D=created_at:desc",
        "nintendo switch 2": "https://www.olx.pl/oferty/q-nintendo-switch-2/?search%5Border%5D=created_at:desc",
        "playstation 5": "https://www.olx.pl/oferty/q-playstation-5/?search%5Border%5D=created_at:desc",
        "steam deck": "https://www.olx.pl/oferty/q-steam-deck/?search%5Border%5D=created_at:desc",
    },
    "vinted": {
        "xbox series s": "https://www.vinted.pl/catalog?search_text=xbox%20series%20s&order=newest_first&page=1&time={timestamp}",
        "xbox series x": "https://www.vinted.pl/catalog?search_text=xbox%20series%20x&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "nintendo switch": "https://www.vinted.pl/catalog?search_text=nintendo%20switch&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "nintendo switch 2": "https://www.vinted.pl/catalog?search_text=nintendo%20switch%202&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "playstation 5": "https://www.vinted.pl/catalog?search_text=playstation%205&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "steam deck": "https://www.vinted.pl/catalog?search_text=steam%20deck&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
    },
}

```

## `app/db.py`

```python
from __future__ import annotations

import aiosqlite
import logging

from app.models import Offer

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS seen_offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_key TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    price REAL,
                    model TEXT,
                    storage TEXT,
                    condition TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS market_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    storage TEXT NOT NULL DEFAULT '',
                    baseline_price REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model, storage)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_seen_offers_unique_key
                ON seen_offers (unique_key)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_seen_offers_created_at
                ON seen_offers (created_at)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_baselines_model_storage
                ON market_baselines (model, storage)
            """)

            await db.commit()

        logger.info("Baza danych gotowa: %s", self.db_path)

    async def has_seen(self, offer: Offer) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM seen_offers WHERE unique_key = ? LIMIT 1",
                (offer.unique_key,),
            )
            row = await cursor.fetchone()
            await cursor.close()
            return row is not None

    async def mark_seen(self, offer: Offer) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO seen_offers (
                    unique_key, source, url, title, price, model, storage, condition
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                offer.unique_key,
                offer.source,
                offer.url,
                offer.title,
                offer.price,
                offer.model,
                offer.storage,
                offer.condition,
            ))
            await db.commit()

    async def count_seen(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM seen_offers")
            row = await cursor.fetchone()
            await cursor.close()
            return int(row[0] if row else 0)

    async def upsert_market_baseline(
        self,
        model: str,
        storage: str,
        baseline_price: float,
        sample_size: int,
        scope: str,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO market_baselines (
                    model, storage, baseline_price, sample_size, scope, refreshed_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(model, storage) DO UPDATE SET
                    baseline_price = excluded.baseline_price,
                    sample_size = excluded.sample_size,
                    scope = excluded.scope,
                    refreshed_at = CURRENT_TIMESTAMP
            """, (
                (model or "").lower().strip(),
                (storage or "").upper().strip(),
                baseline_price,
                sample_size,
                scope,
            ))
            await db.commit()

    async def get_market_baseline(
        self,
        model: str,
        storage: str,
    ) -> tuple[float, int, str] | None:
        model_norm = (model or "").lower().strip()
        storage_norm = (storage or "").upper().strip()

        if not model_norm:
            return None

        async with aiosqlite.connect(self.db_path) as db:
            if storage_norm:
                cursor = await db.execute("""
                    SELECT baseline_price, sample_size, scope
                    FROM market_baselines
                    WHERE model = ? AND storage = ?
                    LIMIT 1
                """, (model_norm, storage_norm))
                row = await cursor.fetchone()
                await cursor.close()

                if row:
                    return float(row[0]), int(row[1]), str(row[2])

            cursor = await db.execute("""
                SELECT baseline_price, sample_size, scope
                FROM market_baselines
                WHERE model = ? AND storage = ''
                LIMIT 1
            """, (model_norm,))
            row = await cursor.fetchone()
            await cursor.close()

            if row:
                return float(row[0]), int(row[1]), str(row[2])

        return None

    async def clear_market_baselines(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM market_baselines")
            await db.commit()
```

## `app/logging_setup.py`

```python
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

```

## `app/main.py`

```python
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.bot_handlers import setup_handlers
from app.config import get_settings
from app.db import Database
from app.logging_setup import setup_logging
from app.services.flipper_service import FlipperService
from app.services.market_baseline_service import MarketBaselineService

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)

    setup_logging(settings.LOG_LEVEL)
    logger.info("Start aplikacji...")

    db = Database(settings.DATABASE_PATH)
    await db.init()

    bot = Bot(token=settings.TELEGRAM_TOKEN)
    dp = Dispatcher()

    flipper = FlipperService(bot=bot, db=db, settings=settings)
    baseline_service = MarketBaselineService(db=db, settings=settings)

    dp.include_router(setup_handlers(db, flipper))

    scheduler = AsyncIOScheduler(timezone="Europe/Warsaw")

    scheduler.add_job(
        flipper.run_scan,
        trigger=IntervalTrigger(minutes=settings.SCAN_INTERVAL_MINUTES),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
        id="scan_job",
    )

    if settings.ENABLE_MARKET_BASELINE_REFRESH:
        scheduler.add_job(
            baseline_service.refresh_all_baselines,
            trigger=IntervalTrigger(hours=settings.BASELINE_REFRESH_INTERVAL_HOURS),
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
            id="baseline_refresh_job",
        )

    scheduler.start()

    if settings.STARTUP_SCAN:
        asyncio.create_task(flipper.run_scan())

    if settings.ENABLE_MARKET_BASELINE_REFRESH:
        asyncio.create_task(baseline_service.refresh_all_baselines())

    try:
        logger.info("Bot uruchomiony. Polling start.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
```

## `app/models.py`

```python
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib


@dataclass(slots=True)
class Offer:
    source: str
    title: str
    url: str
    price: float
    currency: str = "PLN"
    location: str = ""
    image_url: str = ""
    description: str = ""
    condition: str = ""
    model: str = ""
    storage: str = ""
    color: str = ""
    seller_name: str = ""
    score: float = 0.0

    market_baseline: float = 0.0
    market_sample_size: int = 0
    market_scope: str = ""

    raw_payload: dict = field(default_factory=dict)

    @property
    def unique_key(self) -> str:
        base = f"{self.source}|{self.url}".strip().lower()
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

```

## `app/scrapers/__init__.py`

```python

```

## `app/scrapers/allegro_lokalnie.py`

```python
from __future__ import annotations

import logging

from playwright.async_api import Browser

from app.constants import SEARCH_TARGETS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_model, parse_storage, parse_color, parse_condition
from app.utils.misc import absolute_url, clean_text, normalize_price

logger = logging.getLogger(__name__)


class AllegroLokalnieScraper(BaseScraper):
    source_name = "allegro_lokalnie"

    async def scrape(
        self,
        browser: Browser,
        on_offer: OfferCallback | None = None,
    ) -> list[Offer]:
        offers: list[Offer] = []

        for model_hint, start_url in SEARCH_TARGETS[self.source_name].items():
            page = await self._new_page(browser)
            try:
                await self.goto(page, start_url)
                await page.wait_for_timeout(2000)

                cards = page.locator("a[href*='/oferta/'], a[href*='/ogloszenie/']")
                count = min(await cards.count(), self.settings.MAX_OFFERS_PER_SOURCE)
                logger.info("[%s] %s | liczba kart: %s", self.source_name, model_hint, count)

                for i in range(count):
                    try:
                        card = cards.nth(i)
                        href = await card.get_attribute("href")
                        url = absolute_url("https://allegrolokalnie.pl", href)
                        raw_text = clean_text(await card.inner_text())

                        if not url:
                            continue

                        title = raw_text.split("zł")[0].strip()[:180] if raw_text else ""
                        price = normalize_price(raw_text)

                        img = ""
                        img_el = card.locator("img").first
                        if await img_el.count():
                            src = (await img_el.get_attribute("src") or "").strip()
                            if src.startswith(("http://", "https://")):
                                img = src

                        model = parse_model(title) or model_hint
                        storage = parse_storage(title)
                        color = parse_color(title)
                        condition = parse_condition(raw_text)

                        offer = Offer(
                            source=self.source_name,
                            title=title,
                            url=url,
                            price=price,
                            location="",
                            image_url=img,
                            description="",
                            condition=condition,
                            model=model,
                            storage=storage,
                            color=color,
                            raw_payload={"raw_card_text": raw_text, "query_model": model_hint},
                        )

                        await self.emit_offer(offer, offers, on_offer=on_offer)

                    except Exception:
                        logger.exception("[%s] Nie udało się sparsować karty #%s", self.source_name, i)

            finally:
                await self.close_page(page)

        return offers

```

## `app/scrapers/base.py`

```python
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from playwright.async_api import Browser, Page
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Settings
from app.models import Offer
from app.utils.misc import random_delay_ms

logger = logging.getLogger(__name__)

OfferCallback = Callable[[Offer], Awaitable[None]]


class BaseScraper(ABC):
    source_name: str = "base"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    async def scrape(
        self,
        browser: Browser,
        on_offer: OfferCallback | None = None,
    ) -> list[Offer]:
        raise NotImplementedError

    async def _new_page(self, browser: Browser) -> Page:
        context = await browser.new_context(
            user_agent=self.settings.USER_AGENT,
            locale="pl-PL",
            java_script_enabled=True,
            viewport={"width": 1440, "height": 2400},
        )
        page = await context.new_page()
        page.set_default_timeout(self.settings.PLAYWRIGHT_TIMEOUT_MS)
        return page

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def goto(self, page: Page, url: str) -> None:
        logger.info("[%s] Otwieram URL: %s", self.source_name, url)
        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=self.settings.PLAYWRIGHT_TIMEOUT_MS,
        )
        await page.wait_for_timeout(
            random_delay_ms(self.settings.RANDOM_DELAY_MIN_MS, self.settings.RANDOM_DELAY_MAX_MS)
        )

    async def emit_offer(
        self,
        offer: Offer,
        offers: list[Offer],
        on_offer: OfferCallback | None = None,
    ) -> None:
        offers.append(offer)
        if on_offer is not None:
            await on_offer(offer)

    async def close_page(self, page: Page) -> None:
        try:
            await page.context.close()
        except Exception:
            logger.exception("[%s] Błąd przy zamykaniu contextu", self.source_name)

```

## `app/scrapers/olx.py`

```python
from __future__ import annotations

import logging

from playwright.async_api import Browser

from app.constants import SEARCH_TARGETS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_model, parse_storage, parse_color, parse_condition
from app.utils.misc import absolute_url, clean_text, normalize_price

logger = logging.getLogger(__name__)


class OLXScraper(BaseScraper):
    source_name = "olx"

    async def scrape(
        self,
        browser: Browser,
        on_offer: OfferCallback | None = None,
    ) -> list[Offer]:
        offers: list[Offer] = []

        for model_hint, start_url in SEARCH_TARGETS[self.source_name].items():
            page = await self._new_page(browser)
            try:
                await self.goto(page, start_url)
                await page.wait_for_timeout(2000)

                cards = page.locator("div[data-cy='l-card'], div[data-testid='l-card']")
                count = min(await cards.count(), self.settings.MAX_OFFERS_PER_SOURCE)
                logger.info("[%s] %s | liczba kart: %s", self.source_name, model_hint, count)

                for i in range(count):
                    try:
                        card = cards.nth(i)
                        link = card.locator("a[href]").first
                        href = await link.get_attribute("href")
                        url = absolute_url("https://www.olx.pl", href)

                        title = ""
                        title_loc = card.locator("h4, h6").first
                        if await title_loc.count():
                            title = clean_text(await title_loc.inner_text())

                        price_text = ""
                        price_loc = card.locator("p[data-testid='ad-price'], p").first
                        if await price_loc.count():
                            price_text = clean_text(await price_loc.inner_text())

                        location_text = ""
                        location_locator = card.locator("p[data-testid='location-date'], p")
                        if await location_locator.count():
                            all_text = clean_text(await location_locator.last.inner_text())
                            location_text = all_text.split("-")[0].strip()

                        img = ""
                        img_el = card.locator("img").first
                        if await img_el.count():
                            src = (await img_el.get_attribute("src") or "").strip()
                            if src.startswith(("http://", "https://")):
                                img = src

                        price = normalize_price(price_text)
                        model = parse_model(title) or model_hint
                        storage = parse_storage(title)
                        color = parse_color(title)
                        condition = parse_condition(title)

                        offer = Offer(
                            source=self.source_name,
                            title=title,
                            url=url,
                            price=price,
                            location=location_text,
                            image_url=img,
                            description="",
                            condition=condition,
                            model=model,
                            storage=storage,
                            color=color,
                            raw_payload={"price_text": price_text, "query_model": model_hint},
                        )

                        await self.emit_offer(offer, offers, on_offer=on_offer)

                    except Exception:
                        logger.exception("[%s] Nie udało się sparsować karty #%s", self.source_name, i)

            finally:
                await self.close_page(page)

        return offers

```

## `app/scrapers/vinted.py`

```python
from __future__ import annotations

import asyncio
import logging

from playwright.async_api import Browser

from app.constants import SEARCH_TARGETS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_model, parse_storage, parse_color, parse_condition
from app.utils.misc import absolute_url, clean_text, normalize_price, build_vinted_timestamped_url

logger = logging.getLogger(__name__)


class VintedScraper(BaseScraper):
    source_name = "vinted"

    async def scrape(
        self,
        browser: Browser,
        on_offer: OfferCallback | None = None,
    ) -> list[Offer]:
        offers: list[Offer] = []
        semaphore = asyncio.Semaphore(self.settings.CONCURRENT_DETAIL_PAGES)

        for model_hint, template_url in SEARCH_TARGETS[self.source_name].items():
            page = await self._new_page(browser)
            try:
                start_url = build_vinted_timestamped_url(template_url)
                logger.info("[%s] start_url=%s", self.source_name, start_url)
                await self.goto(page, start_url)
                await page.wait_for_timeout(3500)

                cards = page.locator("a[href*='/items/']")
                count = await cards.count()
                logger.info("[%s] %s | liczba linków do ofert: %s", self.source_name, model_hint, count)

                urls: list[str] = []
                for i in range(min(count, self.settings.MAX_OFFERS_PER_SOURCE)):
                    try:
                        href = await cards.nth(i).get_attribute("href")
                        url = absolute_url("https://www.vinted.pl", href)
                        if url and url not in urls:
                            urls.append(url)
                    except Exception:
                        logger.exception("[%s] Nie udało się pobrać href dla karty #%s", self.source_name, i)

                async def process_detail(url: str) -> None:
                    async with semaphore:
                        detail_page = await self._new_page(browser)
                        try:
                            await self.goto(detail_page, url)
                            await detail_page.wait_for_timeout(1800)

                            title = await self._extract_title(detail_page)
                            full_text = clean_text(await detail_page.locator("body").inner_text())
                            price = await self._extract_price(detail_page)
                            image_url = await self._extract_image(detail_page)
                            description = await self._extract_description(detail_page)
                            location = self._extract_location_from_text(full_text)
                            details = await self._extract_details_map(detail_page)

                            detail_storage = clean_text(details.get("pamięć", "")) or clean_text(details.get("pamiec", ""))
                            detail_condition = clean_text(details.get("stan", ""))
                            detail_color = clean_text(details.get("kolor", ""))
                            detail_added = clean_text(details.get("dodane", ""))

                            model = parse_model(title) or parse_model(description) or model_hint
                            storage = parse_storage(detail_storage) or parse_storage(f"{title} {description}".strip())
                            condition = clean_text(detail_condition) or parse_condition(f"{title} {description}".strip())
                            color = clean_text(detail_color) or parse_color(f"{title} {description}".strip())

                            final_description = (description or "").strip()
                            if detail_added:
                                extra = f"Dodane: {detail_added}"
                                final_description = f"{final_description}\n{extra}".strip()

                            offer = Offer(
                                source=self.source_name,
                                title=title or "Oferta z Vinted",
                                url=url,
                                price=price,
                                location=location,
                                image_url=image_url,
                                description=final_description,
                                condition=condition,
                                model=model,
                                storage=storage,
                                color=color,
                                raw_payload={
                                    "full_text": full_text[:2000],
                                    "details": details,
                                    "query_model": model_hint,
                                },
                            )

                            await self.emit_offer(offer, offers, on_offer=on_offer)

                        except Exception:
                            logger.exception("[%s] Błąd podczas parsowania detail page: %s", self.source_name, url)
                        finally:
                            await self.close_page(detail_page)

                await asyncio.gather(*(process_detail(url) for url in urls))

            finally:
                await self.close_page(page)

        logger.info("[%s] Łącznie ofert po detail page: %s", self.source_name, len(offers))
        return offers

    async def _extract_title(self, page) -> str:
        selectors = [
            "h1",
            "[data-testid='item-page-title']",
            "div[class*='title']",
            "meta[property='og:title']",
        ]

        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    if selector.startswith("meta"):
                        value = (await loc.get_attribute("content") or "").strip()
                    else:
                        value = await loc.inner_text()
                    value = clean_text(value)
                    if value:
                        return value
            except Exception:
                continue

        return ""

    async def _extract_price(self, page) -> float:
        selectors = [
            "[data-testid='item-price']",
            "div[class*='price']",
            "span[class*='price']",
            "meta[property='product:price:amount']",
        ]

        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    if selector.startswith("meta"):
                        value = clean_text(await loc.get_attribute("content"))
                    else:
                        value = clean_text(await loc.inner_text())

                    price = normalize_price(value)
                    if 50 <= price <= 30000:
                        return price
            except Exception:
                continue

        return 0.0

    async def _extract_image(self, page) -> str:
        try:
            meta = page.locator("meta[property='og:image']").first
            if await meta.count():
                content = (await meta.get_attribute("content") or "").strip()
                if content.startswith(("http://", "https://")):
                    return content
        except Exception:
            pass

        try:
            imgs = page.locator("img")
            img_count = await imgs.count()
            for i in range(min(img_count, 12)):
                src = (await imgs.nth(i).get_attribute("src") or "").strip()
                if not src.startswith(("http://", "https://")):
                    continue
                lowered = src.lower()
                if any(part in lowered for part in ["avatar", "icon", "logo", "default", "profile", "user"]):
                    continue
                return src
        except Exception:
            pass

        return ""

    async def _extract_description(self, page) -> str:
        selectors = [
            "[data-testid='item-description']",
            "div[class*='description']",
            "section p",
            "section",
        ]

        bad_snippets = [
            "strona główna",
            "przedmioty użytkownika",
            "podobne rzeczy",
        ]

        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue

                value = clean_text(await loc.inner_text())
                if not value:
                    continue

                lower_value = value.lower()
                if any(snippet in lower_value for snippet in bad_snippets):
                    continue

                if len(value) > 650:
                    value = value[:650].strip()

                if len(value) < 10:
                    continue

                return value
            except Exception:
                continue

        return ""

    async def _extract_details_map(self, page) -> dict[str, str]:
        details: dict[str, str] = {}

        body_text = clean_text(await page.locator("body").inner_text())
        lines = [line.strip() for line in body_text.split("\n") if line.strip()]

        wanted_keys = {
            "marka", "model", "pamięć", "pamiec", "stan", "kolor", "dodane",
        }

        for i in range(len(lines) - 1):
            key = lines[i].lower().strip().rstrip(":")
            value = lines[i + 1].strip()

            if key in wanted_keys and key not in details:
                details[key] = clean_text(value)

        return details

    def _extract_location_from_text(self, full_text: str) -> str:
        lowered = full_text.lower()
        cities = [
            "warszawa", "kraków", "krakow", "wrocław", "wroclaw", "poznań", "poznan", "gdańsk",
            "gdansk", "łódź", "lodz", "szczecin", "bydgoszcz", "lublin", "katowice", "gdynia", "sopot"
        ]

        for city in cities:
            if city in lowered:
                return city.title()

        return ""

```

## `app/services/__init__.py`

```python

```

## `app/services/flipper_service.py`

```python
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Settings
from app.db import Database
from app.models import Offer
from app.scrapers.allegro_lokalnie import AllegroLokalnieScraper
from app.scrapers.olx import OLXScraper
from app.scrapers.vinted import VintedScraper
from app.services.translator_service import TranslatorService
from app.utils.filters import offer_passes_basic_filters, is_location_preferred
from app.utils.formatting import build_offer_caption, build_offer_keyboard

logger = logging.getLogger(__name__)


class FlipperService:
    def __init__(self, bot: Bot, db: Database, settings: Settings) -> None:
        self.bot = bot
        self.db = db
        self.settings = settings
        self.translator = TranslatorService(target_lang=settings.TRANSLATE_TO_LANGUAGE)
        self._scan_lock = asyncio.Lock()
        self._process_lock = asyncio.Lock()
        self._processing_keys: set[str] = set()

    def _get_scrapers(self):
        scrapers = []
        if self.settings.ENABLE_VINTED:
            scrapers.append(VintedScraper(self.settings))
        if self.settings.ENABLE_OLX:
            scrapers.append(OLXScraper(self.settings))
        if self.settings.ENABLE_ALLEGRO_LOKALNIE:
            scrapers.append(AllegroLokalnieScraper(self.settings))
        return scrapers

    async def run_scan(self) -> None:
        if self._scan_lock.locked():
            logger.warning("Poprzedni scan jeszcze trwa — pomijam kolejne wywołanie.")
            return

        async with self._scan_lock:
            logger.info("=== START SCAN ===")
            self._processing_keys.clear()

            scrapers = self._get_scrapers()
            if not scrapers:
                logger.warning("Brak aktywnych scraperów.")
                return

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.settings.HEADLESS,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )

                try:
                    tasks = [
                        asyncio.create_task(self._run_single_scraper(scraper, browser))
                        for scraper in scrapers
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for scraper, result in zip(scrapers, results):
                        if isinstance(result, Exception):
                            logger.exception(
                                "Scraper %s zakończył się błędem",
                                scraper.source_name,
                                exc_info=result,
                            )
                        else:
                            logger.info(
                                "Scraper %s zakończył pracę | zebrano=%s",
                                scraper.source_name,
                                result,
                            )
                finally:
                    await browser.close()

            logger.info("=== KONIEC SCAN ===")

    async def _run_single_scraper(self, scraper, browser) -> int:
        logger.info("Start scrapera: %s", scraper.source_name)
        offers = await scraper.scrape(browser, on_offer=self.process_offer)
        logger.info(
            "Koniec scrapera: %s | ofert łącznie=%s",
            scraper.source_name,
            len(offers),
        )
        return len(offers)

    async def process_offer(self, offer: Offer) -> None:
        if not offer.url:
            return

        async with self._process_lock:
            if offer.unique_key in self._processing_keys:
                logger.info("Pomijam duplikat w bieżącym skanie: %s", offer.url)
                return
            self._processing_keys.add(offer.unique_key)

        try:
            logger.info(
                "RAW | source=%s | model=%s | storage=%s | price=%s | title=%s | url=%s",
                offer.source,
                offer.model,
                offer.storage,
                offer.price,
                offer.title,
                offer.url,
            )

            if not offer_passes_basic_filters(offer, self.settings):
                logger.info("FILTER OUT | source=%s | title=%s", offer.source, offer.title)
                return

            if self.settings.ENABLE_TRANSLATION:
                offer.description = self.translator.normalize_description_for_post(offer.description)

            baseline_data = await self.db.get_market_baseline(
                model=offer.model,
                storage=offer.storage,
            )

            if baseline_data:
                baseline_price, sample_size, scope = baseline_data
                offer.market_baseline = baseline_price
                offer.market_sample_size = sample_size
                offer.market_scope = scope

                if baseline_price > 0:
                    offer.score = round((baseline_price - offer.price) / baseline_price, 4)
            else:
                offer.score = 0.0

            if is_location_preferred(offer.location, self.settings):
                offer.score += 0.02

            if offer.score < self.settings.MIN_DEAL_SCORE:
                logger.info(
                    "SCORE OUT | source=%s | score=%s | baseline=%s | title=%s",
                    offer.source,
                    offer.score,
                    offer.market_baseline,
                    offer.title,
                )
                return

            if await self.db.has_seen(offer):
                logger.info("Pomijam seen offer: %s", offer.url)
                return

            logger.info(
                "FILTERED | source=%s | model=%s | storage=%s | price=%s | score=%s | baseline=%s | title=%s",
                offer.source,
                offer.model,
                offer.storage,
                offer.price,
                offer.score,
                offer.market_baseline,
                offer.title,
            )

            await self.publish_offer(offer)
            await self.db.mark_seen(offer)

        except Exception:
            logger.exception("Błąd przy procesowaniu oferty: %s", offer.url)
        finally:
            async with self._process_lock:
                self._processing_keys.discard(offer.unique_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def publish_offer(self, offer: Offer) -> None:
        caption = build_offer_caption(offer, self.settings)
        keyboard = build_offer_keyboard(offer)

        logger.info(
            "Publikuję ofertę: %s | %s | %s | %.2f",
            offer.source,
            offer.model,
            offer.storage,
            offer.price,
        )

        image_url = (offer.image_url or "").strip()
        has_valid_image = image_url.startswith(("http://", "https://"))

        if has_valid_image:
            try:
                await self.bot.send_photo(
                    chat_id=self.settings.CHANNEL_ID,
                    photo=image_url,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                logger.info("Wysłano przez send_photo: %s", offer.url)
                return
            except Exception as e:
                logger.exception(
                    "Błąd send_photo dla %s | image_url=%s | error=%s",
                    offer.url,
                    image_url,
                    e,
                )

        await self.bot.send_message(
            chat_id=self.settings.CHANNEL_ID,
            text=caption,
            parse_mode="HTML",
            disable_web_page_preview=False,
            reply_markup=keyboard,
        )
        logger.info("Wysłano przez send_message: %s", offer.url)

```

## `app/services/market_baseline_service.py`

```python
from __future__ import annotations

import logging
from statistics import median
from urllib.parse import quote

from playwright.async_api import async_playwright

from app.config import Settings
from app.constants import CONSOLE_MODELS
from app.db import Database
from app.models import Offer
from app.scrapers.allegro_lokalnie import AllegroLokalnieScraper
from app.scrapers.olx import OLXScraper
from app.scrapers.vinted import VintedScraper
from app.utils.console_parser import parse_model, parse_storage

logger = logging.getLogger(__name__)

STORAGES = ["64GB", "128GB", "256GB", "512GB", "1TB"]


class MarketBaselineService:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    async def refresh_all_baselines(self) -> None:
        logger.info("=== START REFRESH BAZOWYCH CEN ===")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.settings.HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            try:
                for model in CONSOLE_MODELS:
                    await self._refresh_model_only(browser, model)

                    if model in {"steam deck", "nintendo switch", "nintendo switch 2"}:
                        for storage in STORAGES:
                            await self._refresh_model_storage(browser, model, storage)
            finally:
                await browser.close()

        logger.info("=== KONIEC REFRESH BAZOWYCH CEN ===")

    async def _refresh_model_only(self, browser, model: str) -> None:
        offers = await self._collect_market_offers(browser, model=model, storage="")
        prices = self._extract_prices_for_exact_match(offers, model, "")

        if len(prices) < self.settings.BASELINE_MIN_SAMPLES_FOR_MODEL:
            logger.info("[baseline] Za mało danych dla model=%s | samples=%s", model, len(prices))
            return

        baseline = self._calculate_baseline(prices)
        if baseline <= 0:
            return

        await self.db.upsert_market_baseline(
            model=model,
            storage="",
            baseline_price=baseline,
            sample_size=len(prices),
            scope="model",
        )
        logger.info("[baseline] model=%s | baseline=%s | samples=%s", model, baseline, len(prices))

    async def _refresh_model_storage(self, browser, model: str, storage: str) -> None:
        offers = await self._collect_market_offers(browser, model=model, storage=storage)
        prices = self._extract_prices_for_exact_match(offers, model, storage)

        if len(prices) < self.settings.BASELINE_MIN_SAMPLES_FOR_STORAGE:
            logger.info(
                "[baseline] Za mało danych dla model=%s storage=%s | samples=%s",
                model, storage, len(prices)
            )
            return

        baseline = self._calculate_baseline(prices)
        if baseline <= 0:
            return

        await self.db.upsert_market_baseline(
            model=model,
            storage=storage,
            baseline_price=baseline,
            sample_size=len(prices),
            scope="model+storage",
        )
        logger.info(
            "[baseline] model=%s | storage=%s | baseline=%s | samples=%s",
            model, storage, baseline, len(prices)
        )

    async def _collect_market_offers(self, browser, model: str, storage: str) -> list[Offer]:
        query = f"{model} {storage}".strip()
        offers: list[Offer] = []

        if self.settings.ENABLE_VINTED:
            scraper = VintedScraper(self.settings)
            offers.extend(await scraper.scrape(browser))

        if self.settings.ENABLE_OLX:
            scraper = OLXScraper(self.settings)
            offers.extend(await scraper.scrape(browser))

        if self.settings.ENABLE_ALLEGRO_LOKALNIE:
            scraper = AllegroLokalnieScraper(self.settings)
            offers.extend(await scraper.scrape(browser))

        filtered: list[Offer] = []
        for offer in offers:
            offer_model = parse_model(f"{offer.model} {offer.title} {offer.description}".strip()) or offer.model
            offer_storage = parse_storage(f"{offer.storage} {offer.title} {offer.description}".strip()) or offer.storage
            if offer_model != model:
                continue
            if storage and (offer_storage or "").upper().strip() != storage.upper().strip():
                continue
            filtered.append(offer)

        unique = {}
        for offer in filtered:
            if offer.url and offer.url not in unique:
                unique[offer.url] = offer

        return list(unique.values())[: self.settings.BASELINE_MAX_OFFERS_PER_QUERY]

    def _extract_prices_for_exact_match(self, offers: list[Offer], model: str, storage: str) -> list[float]:
        model_norm = model.lower().strip()
        storage_norm = storage.upper().strip()
        prices: list[float] = []

        for offer in offers:
            if offer.price <= 0:
                continue

            if offer.price < 100 or offer.price > 30000:
                continue

            if (offer.model or "").lower().strip() != model_norm:
                continue

            if storage_norm and (offer.storage or "").upper().strip() != storage_norm:
                continue

            prices.append(float(offer.price))

        return self._remove_outliers(prices)

    def _remove_outliers(self, prices: list[float]) -> list[float]:
        if len(prices) < 6:
            return prices

        sorted_prices = sorted(prices)
        cut = max(1, int(len(sorted_prices) * 0.1))
        trimmed = sorted_prices[cut:-cut]
        return trimmed if trimmed else sorted_prices

    def _calculate_baseline(self, prices: list[float]) -> float:
        if not prices:
            return 0.0
        return round(float(median(prices)), 2)

    def _build_vinted_url(self, query: str) -> str:
        return f"https://www.vinted.pl/catalog?search_text={quote(query)}"

    def _build_olx_url(self, query: str) -> str:
        slug = quote(query.replace(" ", "-"))
        return f"https://www.olx.pl/oferty/q-{slug}/"

    def _build_allegro_url(self, query: str) -> str:
        slug = quote(query)
        return f"https://allegrolokalnie.pl/oferty/q/{slug}?sort=startingTime-desc"

```

## `app/services/scoring.py`

```python
from __future__ import annotations

from app.models import Offer


def calculate_offer_score(offer: Offer, reference_prices: dict[str, float]) -> float:
    """
    Score > 0 oznacza, że oferta jest tańsza od ceny referencyjnej.
    Im wyższy score, tym lepsza okazja.
    """
    if offer.price <= 0:
        return 0.0

    model = (offer.model or "").lower()
    reference = reference_prices.get(model)
    if not reference or reference <= 0:
        return 0.0

    score = (reference - offer.price) / reference

    # Delikatny bonus za preferowaną lokalizację będzie doklejany osobno.
    return round(score, 4)
```

## `app/services/translator_service.py`

```python
from __future__ import annotations

import logging

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


class TranslatorService:
    def __init__(self, target_lang: str = "pl") -> None:
        self.target_lang = target_lang

    def detect_language(self, text: str) -> str:
        text = (text or "").strip()
        if not text or len(text) < 8:
            return "unknown"

        try:
            return detect(text)
        except LangDetectException:
            return "unknown"
        except Exception:
            logger.exception("Błąd wykrywania języka")
            return "unknown"

    def translate_to_polish(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""

        lang = self.detect_language(text)
        if lang in {"pl", "unknown"}:
            return text

        try:
            translated = GoogleTranslator(source="auto", target="pl").translate(text)
            return (translated or text).strip()
        except Exception:
            logger.exception("Błąd tłumaczenia tekstu")
            return text

    def normalize_description_for_post(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""

        text = self.translate_to_polish(text)
        text = " ".join(text.split())
        return text[:500]
```

## `app/utils/__init__.py`

```python

```

## `app/utils/console_parser.py`

```python
from __future__ import annotations

import re

from app.constants import COLOR_KEYWORDS, CONDITION_KEYWORDS, CONSOLE_MODELS, MODEL_ALIASES, STORAGE_PATTERNS
from app.utils.misc import clean_text


def parse_model(text: str) -> str:
    value = clean_text(text).lower()
    value = value.replace("sony ", "").replace("microsoft ", "")

    for model in CONSOLE_MODELS:
        aliases = MODEL_ALIASES.get(model, [])
        if any(alias in value for alias in aliases):
            return model

    if re.search(r"\bps5\b", value):
        return "playstation 5"

    if re.search(r"\bxsx\b", value):
        return "xbox series x"

    if re.search(r"\bxss\b", value):
        return "xbox series s"

    return ""


def parse_storage(text: str) -> str:
    value = clean_text(text).lower().replace(" ", "")
    for item in STORAGE_PATTERNS:
        if item in value:
            return item.upper()

    match = re.search(r"\b(64|128|256|512)\s*gb\b", value, re.IGNORECASE)
    if match:
        return f"{match.group(1)}GB"

    match = re.search(r"\b1\s*tb\b", value, re.IGNORECASE)
    if match:
        return "1TB"

    return ""


def parse_color(text: str) -> str:
    value = clean_text(text).lower()
    for color in sorted(COLOR_KEYWORDS, key=len, reverse=True):
        if color in value:
            return color.title()
    return ""


def parse_condition(text: str) -> str:
    value = clean_text(text).lower()
    for label, keywords in CONDITION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in value:
                return label
    return ""

```

## `app/utils/filters.py`

```python
from __future__ import annotations

import re

from app.config import Settings
from app.models import Offer

ACCESSORY_KEYWORDS = [
    "etui", "case", "pokrowiec", "obudowa", "skórka", "nakładka", "nakladka", "folia", "szkło",
    "szklo", "ładowarka", "ladowarka", "zasilacz", "kabel", "adapter", "uchwyt", "stojak",
    "stacja dokująca", "stacja dokujaca", "dock", "dok", "base", "uchwyt", "pokrywa",
    "pad", "pady", "kontroler", "kontrolery", "controller", "joy-con", "joy con", "joycon",
    "dualsense", "gamepad", "sluchawki", "słuchawki", "mikrofon", "kamera", "kamerka",
    "pudełko", "pudelko", "karton", "box", "sam box", "samo pudełko", "sam karton",
]

GAME_KEYWORDS = [
    "gra", "gry", "game", "games", "fifa", "ea fc", "fortnite", "zelda", "mario", "spiderman",
    "god of war", "forza", "minecraft", "cyberpunk", "call of duty", "cod ", "gta", "pokemon",
]

PARTS_KEYWORDS = [
    "na części", "na czesci", "części", "czesci", "część", "czesc", "uszkodzona", "uszkodzony",
    "nie działa", "nie dziala", "do naprawy", "na części", "plyta", "płyta", "hdmi port",
    "port hdmi", "wentylator", "obudowa dolna", "taśma", "tasma", "matryca", "lcd",
]

POSITIVE_CONSOLE_HINTS = [
    "konsola", "komplet", "zestaw", "sprzedam konsole", "sprzedam konsolę", "sprzedam ps5",
    "sprzedam xbox", "sprzedam switch", "z padem", "z kontrolerem", "z joy-conami",
    "w zestawie", "pełny zestaw", "pelny zestaw",
]


def is_location_preferred(location: str, settings: Settings) -> bool:
    loc = (location or "").lower()
    if not loc:
        return False

    if any(city in loc for city in settings.preferred_locations_list):
        return True

    if any(region in loc for region in settings.preferred_regions_list):
        return True

    return False


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _word_boundary_contains(text: str, keyword: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


def looks_like_accessory_or_part(offer: Offer) -> bool:
    title = (offer.title or "").lower().strip()
    desc = (offer.description or "").lower().strip()
    blob = f"{title} {desc}".strip()

    if not offer.model:
        return True

    if _contains_any(title, PARTS_KEYWORDS):
        return True

    if _contains_any(title, GAME_KEYWORDS):
        return True

    if _contains_any(title, ACCESSORY_KEYWORDS):
        positive = _contains_any(title, ["konsola", "zestaw", "komplet"]) or _contains_any(desc, POSITIVE_CONSOLE_HINTS)
        if not positive:
            return True

    if offer.price and offer.price < 220:
        if _contains_any(blob, ACCESSORY_KEYWORDS + GAME_KEYWORDS + PARTS_KEYWORDS):
            return True

    accessory_only_patterns = [
        "do ps5", "do playstation 5", "do xbox series x", "do xbox series s", "do switch", "do steam deck",
    ]
    if any(p in title for p in accessory_only_patterns):
        return True

    return False


def offer_passes_basic_filters(offer: Offer, settings: Settings) -> bool:
    blob = f"{offer.title} {offer.description}".lower()

    if looks_like_accessory_or_part(offer):
        return False

    if settings.only_models_list and offer.model.lower() not in settings.only_models_list:
        return False

    if any(keyword in blob for keyword in settings.excluded_keywords_list):
        return False

    if offer.price < settings.MIN_PRICE:
        return False

    if offer.price > settings.MAX_PRICE:
        return False

    model_cap = settings.max_price_by_model.get(offer.model.lower())
    if model_cap is not None and offer.price > model_cap:
        return False

    return True

```

## `app/utils/formatting.py`

```python
from __future__ import annotations

import html

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.constants import PLATFORM_NAMES
from app.models import Offer
from app.utils.filters import is_location_preferred
from app.config import Settings


def build_offer_caption(offer: Offer, settings: Settings) -> str:
    preferred_badge = " ✅ preferowana lokalizacja" if is_location_preferred(offer.location, settings) else ""

    parts = [
        "🎮 <b>Console Flipper Bot — okazja</b>",
        "",
        f"<b>Model:</b> {html.escape(offer.model or 'Nie rozpoznano')}",
        f"<b>Pamięć:</b> {html.escape(offer.storage or 'Brak danych')}",
        f"<b>Kolor:</b> {html.escape(offer.color or 'Brak danych')}",
        f"<b>Cena:</b> <b>{offer.price:.0f} {html.escape(offer.currency)}</b>",
    ]

    if offer.market_baseline > 0:
        if offer.market_scope == "model+storage":
            scope_label = f"{offer.model} {offer.storage}".strip()
        else:
            scope_label = offer.model

        parts.append(
            f"<b>Score okazji:</b> {offer.score:.1%} "
            f"(mediana {html.escape(scope_label)} z {offer.market_sample_size} ofert: "
            f"{offer.market_baseline:.0f} {html.escape(offer.currency)})"
        )
    else:
        parts.append(f"<b>Score okazji:</b> {offer.score:.1%}")

    parts.extend([
        f"<b>Lokalizacja:</b> {html.escape(offer.location or 'Brak danych')}{preferred_badge}",
        f"<b>Platforma:</b> {html.escape(PLATFORM_NAMES.get(offer.source, offer.source))}",
        f"<b>Stan:</b> {html.escape(offer.condition or 'Brak danych')}",
        "",
        f"<b>Tytuł:</b> {html.escape(offer.title or 'Brak danych')}",
    ])

    clean_description = (offer.description or "").strip()
    if clean_description:
        parts.extend([
            "",
            f"<b>Opis:</b> {html.escape(clean_description[:350])}",
        ])

    parts.extend([
        "",
        f"<b>Link:</b> {html.escape(offer.url)}",
    ])

    return "\n".join(parts)


def build_offer_keyboard(offer: Offer) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Otwórz ogłoszenie", url=offer.url)]
        ]
    )

```

## `app/utils/misc.py`

```python
from __future__ import annotations

import html
import random
import re
import time


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_price(price_text: str | None) -> float:
    if not price_text:
        return 0.0

    text = clean_text(price_text).lower()

    patterns = [
        r"(\d[\d\s]{1,10})\s*zł",
        r"(\d[\d\s]{1,10})\s*pln",
        r"(\d[\d\s]{1,10},\d{2})",
        r"(\d[\d\s]{1,10}\.\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            value = value.replace(" ", "").replace(",", ".")
            try:
                price = float(value)
                if 50 <= price <= 30000:
                    return price
            except ValueError:
                pass

    short_text = text[:100]
    digits = re.findall(r"\d+", short_text)
    if digits:
        joined = "".join(digits[:2])
        try:
            price = float(joined)
            if 50 <= price <= 30000:
                return price
        except ValueError:
            pass

    return 0.0


def absolute_url(base: str, href: str | None) -> str:
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{base.rstrip('/')}/{href.lstrip('/')}"


def build_vinted_timestamped_url(template: str) -> str:
    return template.format(timestamp=int(time.time()))


def random_delay_ms(min_ms: int, max_ms: int) -> int:
    if max_ms <= min_ms:
        return min_ms
    return random.randint(min_ms, max_ms)

```

## `railway.toml`

```python
[build]
builder = "DOCKERFILE"

[deploy]
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

```

## `requirements.txt`

```python
aiogram==3.13.1
APScheduler==3.10.4
playwright==1.47.0
aiosqlite==0.20.0
tenacity==9.0.0
pydantic==2.9.2
pydantic-settings==2.5.2
deep-translator==1.11.4
langdetect==1.0.9

```

