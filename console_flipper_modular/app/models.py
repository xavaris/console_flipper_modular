from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .utils.misc import normalize_url


@dataclass(slots=True)
class Offer:
    source: str
    console_key: str
    title: str
    price: int
    location: str
    url: str
    image_url: str | None
    offer_id: str
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.offer_id}:{normalize_url(self.url)}"


@dataclass(slots=True)
class SearchTarget:
    key: str
    label: str
    emoji: str
    aliases: list[str]
    env_var: str
    default_max_price: int
