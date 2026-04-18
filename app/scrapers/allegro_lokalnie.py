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
