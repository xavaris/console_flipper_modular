from __future__ import annotations

import logging
from statistics import median

from playwright.async_api import async_playwright

from app.config import Settings
from app.constants import CONSOLE_MODELS
from app.db import Database
from app.models import Offer
from app.scrapers.allegro_lokalnie import AllegroLokalnieScraper
from app.scrapers.olx import OLXScraper
from app.scrapers.vinted import VintedScraper
from app.utils.console_parser import parse_model, parse_storage
from app.utils.filters import offer_passes_basic_filters

logger = logging.getLogger(__name__)

STORAGES = ["32GB", "64GB", "128GB", "256GB", "512GB", "1TB"]


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

                    if model in {"steam deck", "nintendo switch", "nintendo switch 2", "playstation portal"}:
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

        await self.db.upsert_market_baseline(model=model, storage="", baseline_price=baseline, sample_size=len(prices), scope="model")
        logger.info("[baseline] model=%s | baseline=%s | samples=%s", model, baseline, len(prices))

    async def _refresh_model_storage(self, browser, model: str, storage: str) -> None:
        offers = await self._collect_market_offers(browser, model=model, storage=storage)
        prices = self._extract_prices_for_exact_match(offers, model, storage)

        if len(prices) < self.settings.BASELINE_MIN_SAMPLES_FOR_STORAGE:
            logger.info("[baseline] Za mało danych dla model=%s storage=%s | samples=%s", model, storage, len(prices))
            return

        baseline = self._calculate_baseline(prices)
        if baseline <= 0:
            return

        await self.db.upsert_market_baseline(model=model, storage=storage, baseline_price=baseline, sample_size=len(prices), scope="model+storage")
        logger.info("[baseline] model=%s | storage=%s | baseline=%s | samples=%s", model, storage, baseline, len(prices))

    async def _collect_market_offers(self, browser, model: str, storage: str) -> list[Offer]:
        offers: list[Offer] = []

        if self.settings.ENABLE_VINTED:
            offers.extend(await VintedScraper(self.settings).scrape(browser))
        if self.settings.ENABLE_OLX:
            offers.extend(await OLXScraper(self.settings).scrape(browser))
        if self.settings.ENABLE_ALLEGRO_LOKALNIE:
            offers.extend(await AllegroLokalnieScraper(self.settings).scrape(browser))

        filtered: list[Offer] = []
        for offer in offers:
            offer.model = parse_model(f"{offer.model} {offer.title} {offer.description}".strip()) or offer.model
            offer.storage = parse_storage(f"{offer.storage} {offer.title} {offer.description}".strip()) or offer.storage

            if offer.model != model:
                continue
            if storage and (offer.storage or "").upper().strip() != storage.upper().strip():
                continue
            if not offer_passes_basic_filters(offer, self.settings):
                continue
            filtered.append(offer)

        unique: dict[str, Offer] = {}
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
