from __future__ import annotations

import asyncio
import logging

from playwright.async_api import Browser, Page

from app.constants import SEARCH_TARGETS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_color, parse_condition, parse_model, parse_storage
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
        semaphore = asyncio.Semaphore(self.settings.CONCURRENT_DETAIL_PAGES)

        for model_hint, start_url in SEARCH_TARGETS[self.source_name].items():
            page = await self._new_page(browser)
            try:
                await self.goto(page, start_url)
                await page.wait_for_timeout(2200)

                cards = page.locator("a[href*='/oferta/'], a[href*='/ogloszenie/']")
                count = min(await cards.count(), self.settings.MAX_OFFERS_PER_SOURCE)
                logger.info("[%s] %s | liczba kart: %s", self.source_name, model_hint, count)

                urls: list[str] = []
                seed_data: dict[str, dict] = {}

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

                        urls.append(url)
                        seed_data[url] = {"title": title, "price": price, "image_url": img, "model_hint": model_hint}
                    except Exception:
                        logger.exception("[%s] Nie udało się sparsować karty #%s", self.source_name, i)

                async def process_detail(url: str) -> None:
                    async with semaphore:
                        detail_page = await self._new_page(browser)
                        try:
                            await self.goto(detail_page, url)
                            await detail_page.wait_for_timeout(1500)

                            seed = seed_data.get(url, {})
                            title = await self._extract_title(detail_page) or seed.get("title", "")
                            description = await self._extract_description(detail_page)
                            detail_text = f"{title} {description}".strip()

                            offer = Offer(
                                source=self.source_name,
                                title=title,
                                url=url,
                                price=await self._extract_price(detail_page, seed.get("price", 0.0)),
                                location=await self._extract_location(detail_page),
                                image_url=await self._extract_image(detail_page) or seed.get("image_url", ""),
                                description=description,
                                condition=parse_condition(detail_text),
                                model=parse_model(detail_text),
                                storage=parse_storage(detail_text),
                                color=parse_color(detail_text),
                                raw_payload={"query_model": seed.get("model_hint", "")},
                            )

                            await self.emit_offer(offer, offers, on_offer=on_offer)
                        except Exception:
                            logger.exception("[%s] Błąd detail page: %s", self.source_name, url)
                        finally:
                            await self.close_page(detail_page)

                await asyncio.gather(*(process_detail(url) for url in urls))
            finally:
                await self.close_page(page)

        return offers

    async def _extract_title(self, page: Page) -> str:
        for selector in ["h1", "meta[property='og:title']"]:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    value = clean_text(await (loc.get_attribute("content") if selector.startswith("meta") else loc.inner_text()))
                    if value:
                        return value
            except Exception:
                continue
        return ""

    async def _extract_price(self, page: Page, fallback: float = 0.0) -> float:
        selectors = ["meta[property='product:price:amount']", "[data-testid='price']", "div[class*='price']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    raw = await (loc.get_attribute("content") if selector.startswith("meta") else loc.inner_text())
                    price = normalize_price(raw)
                    if 50 <= price <= 30000:
                        return price
            except Exception:
                continue
        return float(fallback or 0.0)

    async def _extract_description(self, page: Page) -> str:
        selectors = ["[data-testid='description']", "div[class*='description']", "section[class*='description']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    value = clean_text(await loc.inner_text())
                    if value and len(value) >= 8:
                        return value[:700]
            except Exception:
                continue
        return ""

    async def _extract_location(self, page: Page) -> str:
        selectors = ["[data-testid='location']", "div[class*='location']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    value = clean_text(await loc.inner_text())
                    if value:
                        return value[:120]
            except Exception:
                continue
        return ""

    async def _extract_image(self, page: Page) -> str:
        try:
            meta = page.locator("meta[property='og:image']").first
            if await meta.count():
                value = (await meta.get_attribute("content") or "").strip()
                if value.startswith(("http://", "https://")):
                    return value
        except Exception:
            pass
        return ""
