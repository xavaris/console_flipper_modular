from __future__ import annotations

import logging

from playwright.async_api import Browser

from app.constants import CONSOLE_SEARCH_URLS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_console_model, parse_console_storage, parse_console_color, parse_console_condition
from app.utils.misc import absolute_url, clean_text, normalize_price

logger = logging.getLogger(__name__)


class AllegroLokalnieScraper(BaseScraper):
    source_name = "allegro_lokalnie"

    def __init__(self, settings) -> None:
        super().__init__(settings)
        self.start_urls = CONSOLE_SEARCH_URLS["allegro_lokalnie"]

    async def scrape(
        self,
        browser: Browser,
        on_offer: OfferCallback | None = None,
    ) -> list[Offer]:
        offers: list[Offer] = []
        seen_urls: set[str] = set()

        for model_hint, start_url in self.start_urls.items():
            page = await self._new_page(browser)

            try:
                await self.goto(page, start_url)
                await page.wait_for_timeout(1800)

                cards = page.locator("a[href*='/oferta/'], a[href*='/ogloszenie/']")
                count = min(await cards.count(), self.settings.MAX_OFFERS_PER_SOURCE)
                logger.info("[allegro_lokalnie] model_hint=%s | kart=%s", model_hint, count)

                urls: list[str] = []
                for i in range(count):
                    try:
                        href = await cards.nth(i).get_attribute("href")
                        url = absolute_url("https://allegrolokalnie.pl", href)
                        if url and url not in seen_urls and url not in urls:
                            urls.append(url)
                    except Exception:
                        logger.exception("[allegro_lokalnie] Nie udało się pobrać URL dla karty #%s", i)

                for url in urls:
                    seen_urls.add(url)
                    detail_page = await self._new_page(browser)

                    try:
                        await self.goto(detail_page, url)
                        await detail_page.wait_for_timeout(1200)

                        title = await self._extract_title(detail_page)
                        price = await self._extract_price(detail_page)
                        location = await self._extract_location(detail_page)
                        image_url = await self._extract_image(detail_page)
                        description = await self._extract_description(detail_page)

                        blob = f"{title} {description}".strip()
                        model = parse_console_model(blob)
                        storage = parse_console_storage(blob)
                        color = parse_console_color(blob)
                        condition = parse_console_condition(blob)

                        offer = Offer(
                            source=self.source_name,
                            title=title,
                            url=url,
                            price=price,
                            location=location,
                            image_url=image_url,
                            description=description,
                            condition=condition,
                            model=model,
                            storage=storage,
                            color=color,
                            raw_payload={"model_hint": model_hint},
                        )

                        await self.emit_offer(offer, offers, on_offer=on_offer)

                    except Exception:
                        logger.exception("[allegro_lokalnie] Błąd detail page: %s", url)
                    finally:
                        await self.close_page(detail_page)

            finally:
                await self.close_page(page)

        return offers

    async def _extract_title(self, page) -> str:
        selectors = ["h1", "meta[property='og:title']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                if selector.startswith("meta"):
                    return clean_text(await loc.get_attribute("content"))
                return clean_text(await loc.inner_text())
            except Exception:
                continue
        return ""

    async def _extract_price(self, page) -> float:
        selectors = ["meta[property='product:price:amount']", "h2", "h3", "div"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                if selector.startswith("meta"):
                    raw = await loc.get_attribute("content")
                else:
                    raw = await loc.inner_text()
                price = normalize_price(raw)
                if 50 <= price <= 20000:
                    return price
            except Exception:
                continue
        return 0.0

    async def _extract_location(self, page) -> str:
        try:
            body = clean_text(await page.locator("body").inner_text())
            for marker in ["Lokalizacja", "Odbiór osobisty w", "Miejscowość"]:
                idx = body.find(marker)
                if idx != -1:
                    snippet = body[idx: idx + 160]
                    return clean_text(snippet.replace(marker, ""))[:80]
        except Exception:
            pass
        return ""

    async def _extract_image(self, page) -> str:
        try:
            loc = page.locator("meta[property='og:image']").first
            if await loc.count():
                src = (await loc.get_attribute("content") or "").strip()
                if src.startswith("http://") or src.startswith("https://"):
                    return src
        except Exception:
            pass
        return ""

    async def _extract_description(self, page) -> str:
        selectors = [
            "[data-testid='description']",
            "section",
            "article",
        ]
        bad = ["zobacz podobne", "inne ogłoszenia", "inne ogloszenia"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                value = clean_text(await loc.inner_text())
                if not value or len(value) < 8:
                    continue
                lowered = value.lower()
                if any(x in lowered for x in bad):
                    continue
                return value[:700]
            except Exception:
                continue
        return ""
