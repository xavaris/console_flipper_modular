from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from playwright.async_api import Page

from ..models import Offer, SearchTarget

if TYPE_CHECKING:
    from ..main import RuntimeState

logger = logging.getLogger("console_flipper.scrapers")


class BaseScraper:
    source: str = "base"

    def __init__(self, runtime: "RuntimeState"):
        self.runtime = runtime
        self.config = runtime.config

    async def new_page(self) -> Page:
        assert self.runtime.browser_context is not None
        page = await self.runtime.browser_context.new_page()
        page.set_default_timeout(self.config.request_timeout_seconds * 1000)
        return page

    async def extract(self, target: SearchTarget, max_price: int) -> list[Offer]:
        raise NotImplementedError

    async def _close_page(self, page: Page) -> None:
        try:
            await page.close()
        except Exception:
            logger.exception("Failed to close page for %s", self.source)
