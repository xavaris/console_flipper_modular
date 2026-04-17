from __future__ import annotations

import logging

from ..config import AppConfig
from ..constants import TARGETS
from ..db import StateStore
from ..models import Offer
from .misc import compact_spaces, env_int

logger = logging.getLogger("console_flipper.filters")


class FilterEngine:
    def __init__(self, store: StateStore, config: AppConfig):
        self.store = store
        self.config = config

    async def required_keywords(self) -> list[str]:
        return await self.store.get_list("required_keywords", self.config.default_required_keywords)

    async def blacklist_keywords(self) -> list[str]:
        return await self.store.get_list("blacklist_keywords", self.config.default_blacklist_keywords)

    async def marketplace_flags(self) -> dict[str, bool]:
        default_flags = {
            "vinted": self.config.enable_vinted,
            "olx": self.config.enable_olx,
            "allegro": self.config.enable_allegro,
        }
        saved = await self.store.get_json("marketplace_flags", default_flags)
        return {key: bool(saved.get(key, value)) for key, value in default_flags.items()}

    async def set_marketplace_flag(self, key: str, value: bool) -> dict[str, bool]:
        flags = await self.marketplace_flags()
        if key not in flags:
            raise KeyError(key)
        flags[key] = value
        await self.store.set_json("marketplace_flags", flags)
        return flags

    async def max_prices(self) -> dict[str, int]:
        defaults = {target.key: env_int(__import__("os").getenv(target.env_var), target.default_max_price) for target in TARGETS}
        saved = await self.store.get_json("max_prices", defaults)
        merged: dict[str, int] = {}
        for key, value in defaults.items():
            try:
                merged[key] = int(saved.get(key, value))
            except (TypeError, ValueError):
                merged[key] = value
        return merged

    async def set_max_price(self, console_key: str, price: int) -> dict[str, int]:
        prices = await self.max_prices()
        prices[console_key] = int(price)
        await self.store.set_json("max_prices", prices)
        return prices

    async def is_allowed(self, offer: Offer) -> tuple[bool, str]:
        title = compact_spaces(offer.title).lower()

        blacklist = await self.blacklist_keywords()
        for word in blacklist:
            if word.lower() in title:
                return False, f"blacklist:{word}"

        required = await self.required_keywords()
        if required and not any(word.lower() in title for word in required):
            return False, "required_keywords"

        prices = await self.max_prices()
        max_price = prices.get(offer.console_key)
        if max_price is not None and offer.price > max_price:
            return False, f"price>{max_price}"

        return True, "ok"
