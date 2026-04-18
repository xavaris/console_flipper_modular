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


class OLXScraper(BaseScraper):
    source_name = "olx"

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

                cards = page.locator("div[data-cy='l-card'], div[data-testid='l-card']")
                count = min(await cards.count(), self.settings.MAX_OFFERS_PER_SOURCE)
                logger.info("[%s] %s | liczba kart: %s", self.source_name, model_hint, count)

                urls: list[str] = []
                seed_data: dict[str, dict] = {}

                for i in range(count):
                    try:
                        card = cards.nth(i)
                        link = card.locator("a[href]").first
                        href = await link.get_attribute("href")
                        url = absolute_url("https://www.olx.pl", href)
                        if not url:
                            continue

                        title = clean_text(await card.locator("h4, h6").first.inner_text()) if await card.locator("h4, h6").first.count() else ""
                        price_text = clean_text(await card.locator("p[data-testid='ad-price'], p").first.inner_text()) if await card.locator("p[data-testid='ad-price'], p").first.count() else ""
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

                        urls.append(url)
                        seed_data[url] = {"title": title, "price_text": price_text, "location": location_text, "image_url": img, "model_hint": model_hint}
                    except Exception:
                        logger.exception("[%s] Nie udało się sparsować karty #%s", self.source_name, i)

                async def process_detail(url: str) -> None:
                    async with semaphore:
                        detail_page = await self._new_page(browser)
                        try:
                            await self.goto(detail_page, url)
                            await detail_page.wait_for_timeout(1400)

                            seed = seed_data.get(url, {})
                            title = await self._extract_title(detail_page) or seed.get("title", "")
                            description = await self._extract_description(detail_page)
                            detail_text = f"{title} {description}".strip()

                            offer = Offer(
                                source=self.source_name,
                                title=title,
                                url=url,
                                price=await self._extract_price(detail_page, seed.get("price_text", "")),
                                location=await self._extract_location(detail_page) or seed.get("location", ""),
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
        for selector in ["h1", "[data-cy='ad_title']", "[data-testid='ad-title']"]:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    value = clean_text(await loc.inner_text())
                    if value:
                        return value
            except Exception:
                continue
        return ""

    async def _extract_price(self, page: Page, fallback: str = "") -> float:
        selectors = ["h3", "[data-testid='ad-price-container']", "[data-testid='ad-price']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    value = clean_text(await loc.inner_text())
                    price = normalize_price(value)
                    if 50 <= price <= 30000:
                        return price
            except Exception:
                continue
        return normalize_price(fallback)

    async def _extract_description(self, page: Page) -> str:
        selectors = ["div[data-cy='ad_description']", "[data-testid='ad-description']", "div[class*='description']"]
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
        selectors = ["[data-testid='location-date']", "[data-cy='ad_location']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.count():
                    value = clean_text(await loc.inner_text())
                    if value:
                        return value.split("-")[0].strip()
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
