from __future__ import annotations

import html
import random
import re
import time


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_price(price_text: str | None) -> float:
    if not price_text:
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
                    return price
            except ValueError:
                pass

    short_text = text[:100]
    digits = re.findall(r"\d+", short_text)
    if digits:
        joined = "".join(digits[:2])
        try:
            price = float(joined)
            if 50 <= price <= 30000:
                return price
        except ValueError:
            pass

    return 0.0


def absolute_url(base: str, href: str | None) -> str:
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{base.rstrip('/')}/{href.lstrip('/')}"


def build_vinted_timestamped_url(template: str) -> str:
    return template.format(timestamp=int(time.time()))


def random_delay_ms(min_ms: int, max_ms: int) -> int:
    if max_ms <= min_ms:
        return min_ms
    return random.randint(min_ms, max_ms)
