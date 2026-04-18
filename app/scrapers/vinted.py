from __future__ import annotations

import json
import logging
import re
import time

from playwright.async_api import Browser, Page

from app.constants import CONSOLE_SEARCH_URLS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_console_model, parse_console_storage, parse_console_color, parse_console_condition
from app.utils.misc import absolute_url, clean_text, normalize_price

logger = logging.getLogger(__name__)


class VintedScraper(BaseScraper):
    source_name = "vinted"

    def __init__(self, settings) -> None:
        super().__init__(settings)
        self.start_urls = CONSOLE_SEARCH_URLS["vinted"]

    async def scrape(
        self,
        browser: Browser,
        on_offer: OfferCallback | None = None,
    ) -> list[Offer]:
        offers: list[Offer] = []
        seen_urls: set[str] = set()

        for model_hint, url_template in self.start_urls.items():
            start_url = url_template.format(timestamp=int(time.time()))
            page = await self._new_page(browser)

            try:
                await self.goto(page, start_url)
                await page.wait_for_timeout(3000)

                cards = page.locator("a[href*='/items/']")
                count = min(await cards.count(), self.settings.MAX_OFFERS_PER_SOURCE)
                logger.info("[vinted] model_hint=%s | kart=%s", model_hint, count)

                urls: list[str] = []
                for i in range(count):
                    try:
                        href = await cards.nth(i).get_attribute("href")
                        url = absolute_url("https://www.vinted.pl", href)
                        if url and "/items/" in url and url not in seen_urls and url not in urls:
                            urls.append(url)
                    except Exception:
                        logger.exception("[vinted] Nie udało się pobrać href karty #%s", i)

                for url in urls:
                    seen_urls.add(url)
                    detail_page = await self._new_page(browser)

                    try:
                        await self.goto(detail_page, url)
                        await detail_page.wait_for_timeout(1500)

                        title = await self._extract_title(detail_page)
                        price = await self._extract_price(detail_page)
                        image_url = await self._extract_image(detail_page)
                        description = await self._extract_description(detail_page)
                        details = await self._extract_details_map(detail_page)

                        blob = " ".join(
                            x for x in [
                                title,
                                description,
                                clean_text(details.get("model", "")),
                                clean_text(details.get("pamięć", "")),
                                clean_text(details.get("stan", "")),
                                clean_text(details.get("kolor", "")),
                            ] if x
                        )

                        model = parse_console_model(blob)
                        storage = parse_console_storage(blob)
                        condition = clean_text(details.get("stan", "")) or parse_console_condition(blob)
                        color = clean_text(details.get("kolor", "")) or parse_console_color(blob)
                        location = clean_text(details.get("lokalizacja", ""))

                        offer = Offer(
                            source=self.source_name,
                            title=title or "Oferta z Vinted",
                            url=url,
                            price=price,
                            location=location,
                            image_url=image_url,
                            description=description,
                            condition=condition,
                            model=model,
                            storage=storage,
                            color=color,
                            raw_payload={"model_hint": model_hint, "details": details},
                        )

                        await self.emit_offer(offer, offers, on_offer=on_offer)

                    except Exception:
                        logger.exception("[vinted] Błąd detail page: %s", url)
                    finally:
                        await self.close_page(detail_page)

            finally:
                await self.close_page(page)

        return offers

    async def _extract_title(self, page: Page) -> str:
        selectors = ["h1", "[data-testid='item-page-title']", "meta[property='og:title']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                if selector.startswith("meta"):
                    raw = await loc.get_attribute("content")
                else:
                    raw = await loc.inner_text()
                value = clean_text(raw)
                if value:
                    return value
            except Exception:
                continue
        return ""

    async def _extract_price(self, page: Page) -> float:
        try:
            loc = page.locator("meta[property='product:price:amount']").first
            if await loc.count():
                price = normalize_price(await loc.get_attribute("content"))
                if 50 <= price <= 20000:
                    return price
        except Exception:
            pass

        try:
            scripts = page.locator("script[type='application/ld+json']")
            count = await scripts.count()
            for i in range(count):
                raw_json = await scripts.nth(i).inner_text()
                if not raw_json:
                    continue
                try:
                    data = json.loads(raw_json)
                except Exception:
                    continue

                candidates = data if isinstance(data, list) else [data]
                for item in candidates:
                    if not isinstance(item, dict):
                        continue
                    offers = item.get("offers")
                    if isinstance(offers, dict):
                        price = normalize_price(offers.get("price"))
                        if 50 <= price <= 20000:
                            return price
        except Exception:
            pass

        selectors = ["[data-testid='item-price']", "div[class*='price']", "span[class*='price']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                price = normalize_price(await loc.inner_text())
                if 50 <= price <= 20000:
                    return price
            except Exception:
                continue
        return 0.0

    async def _extract_image(self, page: Page) -> str:
        try:
            loc = page.locator("meta[property='og:image']").first
            if await loc.count():
                src = (await loc.get_attribute("content") or "").strip()
                if src.startswith("http://") or src.startswith("https://"):
                    return src
        except Exception:
            pass
        return ""

    async def _extract_description(self, page: Page) -> str:
        value = await self._extract_description_from_json_ld(page)
        if value:
            return value

        selectors = [
            "[data-testid='item-description']",
            "div[data-testid='item-description']",
            "section[data-testid='item-description']",
            "[itemprop='description']",
            "div[class*='description']",
            "section[class*='description']",
        ]

        candidates: list[str] = []
        for selector in selectors:
            try:
                loc = page.locator(selector)
                count = await loc.count()
                for i in range(min(count, 5)):
                    try:
                        raw = await loc.nth(i).inner_text()
                        value = self._sanitize_description_candidate(raw)
                        if value:
                            candidates.append(value)
                    except Exception:
                        continue
            except Exception:
                continue

        return self._pick_best_description(candidates)

    async def _extract_description_from_json_ld(self, page: Page) -> str:
        try:
            scripts = page.locator("script[type='application/ld+json']")
            count = await scripts.count()
            for i in range(count):
                raw_json = await scripts.nth(i).inner_text()
                if not raw_json:
                    continue
                try:
                    data = json.loads(raw_json)
                except Exception:
                    continue
                objects = data if isinstance(data, list) else [data]
                for obj in objects:
                    if not isinstance(obj, dict):
                        continue
                    value = self._sanitize_description_candidate(obj.get("description"))
                    if value:
                        return value
        except Exception:
            pass
        return ""

    def _sanitize_description_candidate(self, raw: str | None) -> str:
        value = clean_text(raw)
        if not value or len(value) < 10:
            return ""

        lowered = value.lower()
        bad_snippets = [
            "podobne rzeczy", "podobne przedmioty", "przedmioty użytkownika",
            "kup teraz", "zaproponuj cenę", "zapytaj", "ochrona kupujących",
            "wysyłka od", "strona główna", "odzież", "ubrania",
        ]
        if any(x in lowered for x in bad_snippets):
            return ""

        if len(value) > 700:
            value = value[:700].strip()
        return value

    def _pick_best_description(self, candidates: list[str]) -> str:
        if not candidates:
            return ""

        unique: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        scored: list[tuple[int, str]] = []
        for candidate in unique:
            score = self._score_description_candidate(candidate)
            if score > 0:
                scored.append((score, candidate))

        if not scored:
            return ""

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def _score_description_candidate(self, text: str) -> int:
        lowered = text.lower()
        score = 0

        if 25 <= len(text) <= 350:
            score += 8
        elif 351 <= len(text) <= 700:
            score += 5

        good_keywords = [
            "stan", "działa", "dziala", "sprawna", "sprawny", "konsola",
            "sprzedaję", "sprzedaje", "komplet", "pamięć", "pamiec",
            "ładowarka", "pad", "joycon", "portal", "steam deck", "switch",
        ]
        score += sum(2 for x in good_keywords if x in lowered)

        bad_keywords = [
            "tommy hilfiger", "bershka", "shein", "zara", "h&m",
            "xs /", "s /", "m /", "l /", "36 /", "38 /", "40 /",
            "nowy z metką", "nowy bez metki",
        ]
        score -= sum(6 for x in bad_keywords if x in lowered)

        if len(text.split()) <= 4:
            score -= 6

        return score

    async def _extract_details_map(self, page: Page) -> dict[str, str]:
        details: dict[str, str] = {}
        body_text = clean_text(await page.locator("body").inner_text())
        lines = [line.strip() for line in re.split(r"\n+", body_text) if line.strip()]

        wanted_keys = {
            "marka",
            "model",
            "pamięć",
            "pamiec",
            "stan",
            "kolor",
            "dodane",
            "lokalizacja",
            "platforma",
        }

        for i in range(len(lines) - 1):
            key = lines[i].lower().strip().rstrip(":")
            value = lines[i + 1].strip()
            if key in wanted_keys and key not in details:
                details[key] = clean_text(value)

        return details
