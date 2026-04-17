from __future__ import annotations

import asyncio
import logging
from typing import Any, Iterable

from telegram.constants import ParseMode
from telegram.ext import Application

from ..constants import TARGETS
from ..models import Offer
from ..scrapers.allegro_lokalnie import AllegroScraper
from ..scrapers.base import BaseScraper
from ..scrapers.olx import OlxScraper
from ..scrapers.vinted import VintedScraper
from ..utils.filters import FilterEngine
from ..utils.formatting import build_offer_caption
from ..utils.misc import now_ts

logger = logging.getLogger("console_flipper.service")


class ConsoleFlipperService:
    def __init__(self, app: Application, runtime, filters: FilterEngine):
        self.app = app
        self.runtime = runtime
        self.store = runtime.store
        self.filters = filters
        self.scrapers: dict[str, BaseScraper] = {
            "vinted": VintedScraper(runtime),
            "olx": OlxScraper(runtime),
            "allegro": AllegroScraper(runtime),
        }

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.runtime.config.admin_ids

    async def start_loop(self) -> None:
        logger.info("Starting background scraping loop every %ss", self.runtime.config.scrape_interval_seconds)
        while True:
            try:
                if not self.runtime.paused:
                    await self.run_single_check(reason="scheduler")
                await asyncio.sleep(self.runtime.config.scrape_interval_seconds)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Background loop crashed: %s", exc)
                self.runtime.last_error = str(exc)
                await asyncio.sleep(10)

    async def run_single_check(self, reason: str = "manual") -> dict[str, Any]:
        async with self.runtime.check_lock:
            self.runtime.last_check_started_at = now_ts()
            run_id = await self.store.log_run_start()
            marketplace_flags = await self.filters.marketplace_flags()
            max_prices = await self.filters.max_prices()
            discovered_count = 0
            posted_count = 0
            posted_offers: list[Offer] = []

            try:
                logger.info("Check started (%s)", reason)
                tasks = []
                for target in TARGETS:
                    max_price = max_prices[target.key]
                    for market, enabled in marketplace_flags.items():
                        if enabled:
                            tasks.append(self.scrapers[market].extract(target, max_price))

                nested_results = await asyncio.gather(*tasks, return_exceptions=True)
                offers: list[Offer] = []
                for result in nested_results:
                    if isinstance(result, Exception):
                        logger.exception("Scraper task failed", exc_info=result)
                        continue
                    offers.extend(result)

                offers = self._dedupe_by_key(offers)
                offers.sort(key=lambda o: (o.price, o.source, o.title.lower()))
                discovered_count = len(offers)

                for offer in offers:
                    if posted_count >= self.runtime.config.max_posts_per_cycle:
                        break
                    if await self.store.has_seen(offer.dedupe_key):
                        continue
                    allowed, reason_text = await self.filters.is_allowed(offer)
                    if not allowed:
                        logger.info("Offer rejected %s | %s | %s", reason_text, offer.source, offer.title)
                        await self.store.mark_seen(offer)
                        continue

                    sent = await self.publish_offer(offer)
                    await self.store.mark_seen(offer)
                    if sent:
                        posted_count += 1
                        posted_offers.append(offer)

                self.runtime.last_check_finished_at = now_ts()
                self.runtime.last_check_summary = (
                    f"Ostatni check zakończony sukcesem. "
                    f"Znaleziono: {discovered_count}, opublikowano: {posted_count}, powód: {reason}."
                )
                self.runtime.last_error = None
                await self.store.log_run_finish(run_id, "ok", discovered_count, posted_count)
                logger.info("Check finished (%s) found=%s posted=%s", reason, discovered_count, posted_count)
                return {"status": "ok", "discovered": discovered_count, "posted": posted_count, "offers": posted_offers}
            except Exception as exc:
                self.runtime.last_check_finished_at = now_ts()
                self.runtime.last_error = str(exc)
                self.runtime.last_check_summary = f"Błąd podczas checku: {exc}"
                await self.store.log_run_finish(run_id, "error", discovered_count, posted_count, str(exc))
                logger.exception("Check failed (%s): %s", reason, exc)
                raise

    def _dedupe_by_key(self, offers: Iterable[Offer]) -> list[Offer]:
        unique: dict[str, Offer] = {}
        for offer in offers:
            unique.setdefault(offer.dedupe_key, offer)
        return list(unique.values())

    async def publish_offer(self, offer: Offer) -> bool:
        target = next(x for x in TARGETS if x.key == offer.console_key)
        caption = build_offer_caption(target, offer)
        try:
            if offer.image_url and offer.image_url.startswith("http"):
                await self.app.bot.send_photo(
                    chat_id=self.runtime.config.target_chat_id,
                    photo=offer.image_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await self.app.bot.send_message(
                    chat_id=self.runtime.config.target_chat_id,
                    text=caption,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )
            return True
        except Exception as exc:
            logger.exception("Failed to publish offer %s: %s", offer.url, exc)
            self.runtime.last_error = str(exc)
            return False
