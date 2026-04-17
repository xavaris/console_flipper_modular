from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from ..models import Offer, SearchTarget
from ..utils.misc import compact_spaces, parse_price_to_int, slugify
from .base import BaseScraper

logger = logging.getLogger("console_flipper.scrapers.olx")


class OlxScraper(BaseScraper):
    source = "olx"

    async def extract(self, target: SearchTarget, max_price: int) -> list[Offer]:
        results: list[Offer] = []
        for term in target.aliases[:2]:
            page = await self.new_page()
            try:
                url = (
                    "https://www.olx.pl/oferty/q-"
                    f"{quote_plus(term)}/?search%5Border%5D=filter_float_price%3Aasc"
                )
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)

                data = await page.locator('[data-cy="l-card"]').evaluate_all(
                    """
                    (nodes) => nodes.slice(0, 50).map((card) => {
                        const anchor = card.querySelector('a');
                        const img = card.querySelector('img');
                        const text = card.innerText || '';
                        return {
                            href: anchor ? anchor.href : '',
                            title: anchor ? (anchor.getAttribute('title') || anchor.innerText || '') : '',
                            text,
                            image: img ? (img.src || img.getAttribute('src')) : '',
                        };
                    })
                    """
                )
                for item in data:
                    href = item.get("href", "")
                    title = compact_spaces(item.get("title") or item.get("text", "").split("\n")[0])
                    price = parse_price_to_int(item.get("text"))
                    if not href or not title or price is None:
                        continue
                    offer_id_match = re.search(r"-ID([A-Za-z0-9]+)\.html", href)
                    offer_id = offer_id_match.group(1) if offer_id_match else slugify(href)
                    lines = [compact_spaces(x) for x in item.get("text", "").split("\n") if compact_spaces(x)]
                    location = "Polska"
                    for line in reversed(lines):
                        if any(ch.isalpha() for ch in line) and "zł" not in line.lower() and len(line) < 80:
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
                logger.exception("OLX scraping error for %s", target.key)
            finally:
                await self._close_page(page)

        unique = {offer.dedupe_key: offer for offer in results if offer.price <= max_price}
        return sorted(unique.values(), key=lambda x: x.price)
