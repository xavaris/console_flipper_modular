from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from ..models import Offer, SearchTarget
from ..utils.misc import compact_spaces, parse_price_to_int, slugify
from .base import BaseScraper

logger = logging.getLogger("console_flipper.scrapers.vinted")


class VintedScraper(BaseScraper):
    source = "vinted"

    async def extract(self, target: SearchTarget, max_price: int) -> list[Offer]:
        offers: list[Offer] = []
        for term in target.aliases[:2]:
            page = await self.new_page()
            try:
                url = f"https://www.vinted.pl/catalog?search_text={quote_plus(term)}&currency=PLN"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)

                items = await page.locator("a[href*='/items/']").evaluate_all(
                    """
                    (nodes) => nodes.slice(0, 40).map((node) => {
                        const root = node.closest('[data-testid], article, div') || node;
                        const href = node.href || node.getAttribute('href') || '';
                        const img = root.querySelector('img');
                        const text = root.innerText || '';
                        return {
                            href,
                            text,
                            image: img ? (img.src || img.getAttribute('src')) : '',
                        };
                    })
                    """
                )
                for item in items:
                    title = compact_spaces((item.get("text", "").split("\n")[0]))
                    price = parse_price_to_int(item.get("text", ""))
                    href = item.get("href", "")
                    if not title or price is None or not href:
                        continue

                    offer_id_match = re.search(r"/items/(\d+)", href)
                    offer_id = offer_id_match.group(1) if offer_id_match else slugify(href)
                    text = item.get("text", "")
                    location_match = re.findall(
                        r"(?:Warszawa|Kraków|Wrocław|Poznań|Gdańsk|Łódź|Szczecin|Lublin|Katowice|Białystok|Gdynia|Częstochowa|Radom|Polska)",
                        text,
                        flags=re.IGNORECASE,
                    )
                    location = location_match[0] if location_match else "Polska"
                    offers.append(
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
                logger.exception("Vinted scraping error for %s", target.key)
            finally:
                await self._close_page(page)

        unique = {offer.dedupe_key: offer for offer in offers if offer.price <= max_price}
        return sorted(unique.values(), key=lambda x: x.price)
