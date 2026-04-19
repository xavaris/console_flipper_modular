from __future__ import annotations

import re

from app.config import Settings
from app.models import Offer
from app.utils.console_parser import parse_console_model


ACCESSORY_KEYWORDS = [
    "pad", "pady", "kontroler", "kontrolery", "controller", "gamepad",
    "joycon", "joy-con", "dualshock", "dualsense",
    "kierownica", "pedały", "pedaly", "thrustmaster", "fanatec",
    "g29", "g920", "g923",
    "dock", "stacja dokująca", "stacja dokujaca", "stand", "stojak",
    "ładowarka", "ladowarka", "kabel", "zasilacz", "adapter", "uchwyt",
    "etui", "case", "pokrowiec", "obudowa", "cover",
    "pudełko", "pudelko", "karton", "box", "samo pudełko", "samo pudelko",
    "gra", "gry", "game", "games", "cd", "klucz", "key", "konto",
    "obiektyw", "lens", "filtr", "filter", "nd", "uv", "cpl",
]

PARTS_KEYWORDS = [
    "na części", "na czesci", "części", "czesci", "część", "czesc",
    "uszkodzony", "uszkodzona", "nie działa", "nie dziala",
    "naprawa", "na naprawę", "na naprawe",
    "płyta", "plyta", "matryca", "ekran", "gniazdo", "taśma", "tasma",
]

NON_CONSOLE_KEYWORDS = [
    "tv", "telewizor", "monitor", "projektor",
    "xbox one", "xbox 360",
    "ps1", "ps2", "ps3", "ps4",
    "playstation 1", "playstation 2", "playstation 3", "playstation 4",
    "switch lite",
]

BAD_CONSOLE_CONTEXT = [
    "do ps5",
    "do playstation 5",
    "do xbox series x",
    "do xbox series s",
    "do nintendo switch",
    "do steam deck",
    "for ps5",
    "for xbox",
    "for switch",
    "for steam deck",
]

SUSPICIOUS_ONLY_ACCESSORY_TITLES = [
    r"^\s*(pad|kontroler|controller|gamepad|joycon|joy-con|kierownica|dock|stacja|ładowarka|ladowarka|etui|case|gra|gry|filtr|obiektyw)\b",
]


def is_location_preferred(location: str, settings: Settings) -> bool:
    loc = (location or "").lower()
    if not loc:
        return False

    if any(city in loc for city in settings.preferred_locations_list):
        return True

    if any(region in loc for region in settings.preferred_regions_list):
        return True

    return False


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split()).strip()


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _matches_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def looks_like_accessory_or_part(offer: Offer) -> bool:
    title = _normalize(offer.title or "")
    desc = _normalize(offer.description or "")
    url = _normalize(offer.url or "")
    blob = f"{title} {desc} {url}".strip()

    parsed_title_model = parse_console_model(title)

    if _contains_any(blob, ACCESSORY_KEYWORDS):
        return True

    if _contains_any(blob, PARTS_KEYWORDS):
        return True

    if _contains_any(blob, NON_CONSOLE_KEYWORDS):
        return True

    if _contains_any(blob, BAD_CONSOLE_CONTEXT):
        return True

    if _matches_any_pattern(title, SUSPICIOUS_ONLY_ACCESSORY_TITLES):
        return True

    if offer.price and offer.price < 300:
        if _contains_any(blob, ACCESSORY_KEYWORDS):
            return True

    if parsed_title_model and (
        _contains_any(blob, ACCESSORY_KEYWORDS)
        or _contains_any(blob, PARTS_KEYWORDS)
        or _contains_any(blob, BAD_CONSOLE_CONTEXT)
    ):
        return True

    return False


def looks_like_real_console_offer(offer: Offer) -> bool:
    title = _normalize(offer.title or "")
    desc = _normalize(offer.description or "")
    url = _normalize(offer.url or "")
    blob = f"{title} {desc} {url}".strip()

    parsed_title_model = parse_console_model(title)
    parsed_offer_model = (offer.model or "").strip().lower()

    if not parsed_title_model and not parsed_offer_model:
        return False

    if _contains_any(blob, ACCESSORY_KEYWORDS):
        return False

    if _contains_any(blob, PARTS_KEYWORDS):
        return False

    if _contains_any(blob, NON_CONSOLE_KEYWORDS):
        return False

    if _contains_any(blob, BAD_CONSOLE_CONTEXT):
        return False

    return True


def offer_passes_basic_filters(offer: Offer, settings: Settings) -> bool:
    blob = _normalize(f"{offer.title} {offer.description} {offer.url}")

    if looks_like_accessory_or_part(offer):
        return False

    if not looks_like_real_console_offer(offer):
        return False

    if settings.only_models_list and (offer.model or "").lower() not in settings.only_models_list:
        return False

    if any(keyword in blob for keyword in settings.excluded_keywords_list):
        return False

    if offer.price < settings.MIN_PRICE:
        return False

    if offer.price > settings.MAX_PRICE:
        return False

    model_cap = settings.max_price_by_model.get((offer.model or "").lower())
    if model_cap is not None and offer.price > model_cap:
        return False

    return True
