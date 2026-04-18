from __future__ import annotations

import asyncio
import json
import logging
import re

from playwright.async_api import Browser, Page

from app.constants import SEARCH_TARGETS
from app.models import Offer
from app.scrapers.base import BaseScraper, OfferCallback
from app.utils.console_parser import parse_color, parse_condition, parse_model, parse_storage
from app.utils.misc import absolute_url, build_vinted_timestamped_url, clean_text, normalize_price

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
                        if url and "/items/" in url and url not in urls:
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
                            price = await self._extract_price(detail_page)
                            image_url = await self._extract_image(detail_page)
                            description = await self._extract_description(detail_page)
                            details = await self._extract_details_map(detail_page)

                            detail_model = clean_text(details.get("model", ""))
                            detail_storage = clean_text(details.get("pamięć", "")) or clean_text(details.get("pamiec", ""))
                            detail_condition = clean_text(details.get("stan", ""))
                            detail_color = clean_text(details.get("kolor", ""))
                            detail_added = clean_text(details.get("dodane", ""))
                            location = clean_text(details.get("lokalizacja", ""))

                            model_from_title = parse_model(title)
                            model_from_details = parse_model(detail_model)
                            model = model_from_title or model_from_details
                            if not model and model_hint in title.lower():
                                model = model_hint

                            storage = parse_storage(detail_storage)
                            if not storage:
                                storage = parse_storage(f"{title} {description}".strip())

                            condition = detail_condition or parse_condition(f"{title} {description}".strip())
                            color = detail_color or parse_color(f"{title} {description}".strip())

                            final_description = description.strip()
                            if detail_added:
                                final_description = f"{final_description}\nDodane: {detail_added}".strip()

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
                                raw_payload={"details": details, "query_model": model_hint},
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
        selectors = ["h1", "[data-testid='item-page-title']", "meta[property='og:title']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                value = clean_text(await (loc.get_attribute("content") if selector.startswith("meta") else loc.inner_text()))
                if value and len(value) >= 3:
                    return value
            except Exception:
                continue
        return ""

    async def _extract_price(self, page: Page) -> float:
        try:
            loc = page.locator("meta[property='product:price:amount']").first
            if await loc.count():
                raw = await loc.get_attribute("content")
                price = normalize_price(raw)
                if 100 <= price <= 15000:
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

                objects = data if isinstance(data, list) else [data]
                for obj in objects:
                    if not isinstance(obj, dict):
                        continue
                    offers = obj.get("offers")
                    if isinstance(offers, dict):
                        price = normalize_price(offers.get("price"))
                        if 100 <= price <= 15000:
                            return price
        except Exception:
            pass

        selectors = ["[data-testid='item-price']", "div[data-testid*='price']", "span[data-testid*='price']", "div[class*='price']", "span[class*='price']"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                raw = clean_text(await loc.inner_text())
                price = normalize_price(raw)
                if 100 <= price <= 15000:
                    return price
            except Exception:
                continue

        return 0.0

    async def _extract_image(self, page: Page) -> str:
        try:
            meta = page.locator("meta[property='og:image']").first
            if await meta.count():
                content = (await meta.get_attribute("content") or "").strip()
                if content.startswith(("http://", "https://")):
                    return content
        except Exception:
            pass
        return ""

    async def _extract_description(self, page: Page) -> str:
        json_ld_description = await self._extract_description_from_json_ld(page)
        if json_ld_description:
            return json_ld_description

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

        try:
            main = page.locator("main").first
            if await main.count():
                blocks = main.locator("p, div, span")
                count = await blocks.count()
                for i in range(min(count, 80)):
                    try:
                        raw = await blocks.nth(i).inner_text()
                        value = self._sanitize_description_candidate(raw)
                        if value:
                            candidates.append(value)
                    except Exception:
                        continue
        except Exception:
            pass

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
        if not value:
            return ""
        value = re.sub(r"\s+", " ", value).strip()
        lowered = value.lower()
        if len(value) < 12:
            return ""

        bad_snippets = [
            "podobne rzeczy", "podobne przedmioty", "przedmioty użytkownika", "strona główna",
            "kup teraz", "zaproponuj cenę", "zapytaj", "ochronę kupujących", "ochrona kupujących",
            "dowiedz się więcej", "wysyłka od", "dostępna weryfikacja", "opłata za ochronę kupujących",
            "sprzedaj", "zaloguj się", "rejestruj się", "tommy hilfiger", "bershka", "shein",
            "zara", "h&m", "reserved", "stradivarius", "pull&bear",
        ]
        if any(x in lowered for x in bad_snippets):
            return ""

        if re.search(r"\b(xs|s|m|l|xl|xxl)\s*/\s*\d{2}\b", lowered):
            return ""
        if re.search(r"\b\d{2}\s*/\s*\d+\b", lowered):
            return ""

        if len(value) > 700:
            value = value[:700].strip()
        return value

    def _pick_best_description(self, candidates: list[str]) -> str:
        if not candidates:
            return ""

        unique_candidates: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique_candidates.append(item)

        scored: list[tuple[int, str]] = []
        for candidate in unique_candidates:
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
        length = len(text)
        if 30 <= length <= 350:
            score += 8
        elif 351 <= length <= 700:
            score += 5
        elif length < 20:
            score -= 8

        if any(ch in text for ch in [".", ",", ":", ";"]):
            score += 4

        good_keywords = [
            "stan", "bateria", "używania", "uzywania", "rysy", "działa", "dziala",
            "sprzedaję", "sprzedaje", "konsola", "console", "bez", "ślad", "slad",
            "pamięć", "pamiec", "ładowarka", "zestaw", "gry", "pad", "joy-con",
        ]
        score += sum(2 for word in good_keywords if word in lowered)

        bad_keywords = [
            "tommy hilfiger", "bershka", "shein", "zara", "h&m", "reserved",
            "xs /", "s /", "m /", "l /", "36 /", "38 /", "40 /",
            "kup teraz", "zaproponuj cenę", "zapytaj", "wysyłka od",
        ]
        score -= sum(6 for word in bad_keywords if word in lowered)

        if len(text.split()) <= 4:
            score -= 6
        if len(re.findall(r"\d+,\d{2}\s*zł", lowered)) >= 2:
            score -= 8
        return score

    async def _extract_details_map(self, page: Page) -> dict[str, str]:
        details: dict[str, str] = {}
        label_variants = {
            "marka": ["Marka", "Brand"],
            "model": ["Model"],
            "pamięć": ["Pamięć", "Pamiec", "Storage"],
            "stan": ["Stan", "Condition"],
            "kolor": ["Kolor", "Color"],
            "dodane": ["Dodane", "Added"],
            "lokalizacja": ["Lokalizacja", "Location"],
        }

        lines: list[str] = []
        selectors = ["main", "[data-testid='item-page-details']", "aside"]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if not await loc.count():
                    continue
                text = clean_text(await loc.inner_text())
                if not text:
                    continue
                parts = [clean_text(x) for x in re.split(r"\n+", text) if clean_text(x)]
                lines.extend(parts)
            except Exception:
                continue

        deduped_lines: list[str] = []
        seen: set[str] = set()
        for line in lines:
            key = line.lower().strip()
            if key not in seen:
                seen.add(key)
                deduped_lines.append(line)
        lines = deduped_lines

        for canonical_key, variants in label_variants.items():
            for i, line in enumerate(lines[:-1]):
                if line.strip() in variants:
                    value = clean_text(lines[i + 1])
                    if value and len(value) < 120:
                        details[canonical_key] = value
                        break

        return details
