from __future__ import annotations

import html
import random
import re
import time
from typing import Any


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_price(price_text: Any) -> float:
    if price_text is None:
        return 0.0

    if isinstance(price_text, (int, float)):
        price = float(price_text)
        if 50 <= price <= 30000:
            return round(price, 2)
        return 0.0

    text = clean_text(price_text).lower()

    patterns = [
        r"(\d[\d\s]{1,10})\s*zł",
        r"(\d[\d\s]{1,10})\s*pln",
        r"(\d[\d\s]{1,10},\d{2})",
        r"(\d[\d\s]{1,10}\.\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            value = value.replace(" ", "").replace(",", ".")
            try:
                price = float(value)
                if 50 <= price <= 30000:
                    return round(price, 2)
            except ValueError:
                pass

    short_text = text[:120]
    digits = re.findall(r"\d+", short_text)
    if digits:
        joined = "".join(digits[:2])
        try:
            price = float(joined)
            if 50 <= price <= 30000:
                return round(price, 2)
        except ValueError:
            pass

    return 0.0


def absolute_url(base: str, href: str | None) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href
    return f"{base.rstrip('/')}/{href.lstrip('/')}"


def build_vinted_timestamped_url(template: str) -> str:
    return template.format(timestamp=int(time.time()))


def random_delay_ms(min_ms: int, max_ms: int) -> int:
    if max_ms <= min_ms:
        return min_ms
    return random.randint(min_ms, max_ms)
