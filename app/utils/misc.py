from __future__ import annotations

import re
import time


def env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def csv_env(value: str | None, default: str = "") -> list[str]:
    raw = value if value is not None else default
    if not raw.strip():
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def slugify(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return value or "item"


def parse_price_to_int(text: str | None) -> int | None:
    if not text:
        return None
    text = text.replace("\xa0", " ")
    match = re.findall(r"\d[\d\s.,]*", text)
    if not match:
        return None
    raw = match[0].replace(" ", "").replace(",", ".")
    try:
        return int(float(raw))
    except ValueError:
        return None


def first_not_empty(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_url(url: str) -> str:
    return url.split("?")[0].rstrip("/")


def now_ts() -> float:
    return time.time()


def format_ts(ts: float | None) -> str:
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
