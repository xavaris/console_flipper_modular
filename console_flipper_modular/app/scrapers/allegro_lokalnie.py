from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from ..models import Offer, SearchTarget
from ..utils.misc import compact_spaces, parse_price_to_int, slugify
from .base import BaseScraper

logger = logging.getLogger("console_flipper.scrapers.allegro")


class AllegroScraper(BaseScraper):
    source = "allegro"

    async def extract(self, target: SearchTarget, max_price: int) -> list[Offer]:
        results: list[Offer] = []
        for term in target.aliases[:2]:
            page = await self.new_page()
            try:
                url = f"https://allegro.pl/listing?string={quote_plus(term)}&order=p&offerTypeBuyNow=1"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                cards = await page.locator("article").evaluate_all(
                    """
                    (nodes) => nodes.slice(0, 60).map((card) => {
                        const anchor = card.querySelector('a[href*="/oferta/"]');
                        const img = card.querySelector('img');
                        return {
                            href: anchor ? anchor.href : '',
                            title: anchor ? (anchor.innerText || anchor.getAttribute('aria-label') || '') : '',
                            text: card.innerText || '',
                            image: img ? (img.src || img.getAttribute('src')) : '',
                        };
                    })
                    """
                )
                for item in cards:
                    href = item.get("href", "")
                    title = compact_spaces(item.get("title"))
                    text = item.get("text", "")
                    price = parse_price_to_int(text)
                    if not href or not title or price is None:
                        continue

                    lower_text = text.lower()
                    if "odbiór osobisty" not in lower_text and "lokalnie" not in lower_text:
                        continue
                    if "kup teraz" not in lower_text:
                        continue

                    offer_id_match = re.search(r"/oferta/[^/?]+-([A-Za-z0-9]+)", href)
                    offer_id = offer_id_match.group(1) if offer_id_match else slugify(href)

                    location = "Polska"
                    for line in [compact_spaces(x) for x in text.split("\n") if compact_spaces(x)]:
                        low = line.lower()
                        if "odbiór osobisty" in low or "lokalnie" in low:
                            location = line
                            break

                    results.append(
                        Offer(
                            source=self.source,
                            console_key=target.key,
                            title=title,
                            price=price,
                            location=location,
                            url=href,
                            image_url=item.get("image") or None,
                            offer_id=offer_id,
                            raw=item,
                        )
                    )
            except Exception:
                logger.exception("Allegro scraping error for %s", target.key)
            finally:
                await self._close_page(page)

        unique = {offer.dedupe_key: offer for offer in results if offer.price <= max_price}
        return sorted(unique.values(), key=lambda x: x.price)
