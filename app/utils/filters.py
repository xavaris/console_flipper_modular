from __future__ import annotations

import re

from app.config import Settings
from app.models import Offer
from app.utils.console_parser import parse_model

ACCESSORY_KEYWORDS = [
    "etui", "case", "pokrowiec", "obudowa", "skórka", "nakładka", "nakladka", "folia", "szkło",
    "szklo", "ładowarka", "ladowarka", "zasilacz", "kabel", "adapter", "uchwyt", "stojak",
    "stacja dokująca", "stacja dokujaca", "dock", "dok", "base", "pokrywa", "sluchawki",
    "słuchawki", "mikrofon", "kamera", "kamerka", "pudełko", "pudelko", "karton", "box",
    "sam box", "samo pudełko", "sam karton", "pad", "pady", "kontroler", "kontrolery",
    "controller", "joy-con", "joy con", "joycon", "dualsense", "gamepad", "kierownica",
    "pedaly", "pedały", "thrustmaster", "logitech g29", "logitech g920", "filtr", "obiektyw",
]

GAME_KEYWORDS = [
    "gra", "gry", "game", "games", "fifa", "ea fc", "fortnite", "zelda", "mario", "spiderman",
    "god of war", "forza", "minecraft", "cyberpunk", "call of duty", "gta", "pokemon", "pes",
]

PARTS_KEYWORDS = [
    "na części", "na czesci", "części", "czesci", "część", "czesc", "uszkodzona", "uszkodzony",
    "nie działa", "nie dziala", "do naprawy", "plyta", "płyta", "hdmi port", "port hdmi",
    "wentylator", "obudowa dolna", "taśma", "tasma", "matryca", "lcd",
]

NON_CONSOLE_KEYWORDS = [
    "tv", "telewizor", "monitor", "projektor", "laptop", "komputer", "pc", "tablet",
    "router", "drukarka", "airpods", "iphone", "samsung 50 cali", "smart tv",
]

OLDER_OR_WRONG_CONSOLE_KEYWORDS = [
    "playstation 1", "playstation 2", "playstation 3", "playstation 4", "ps1", "ps2", "ps3", "ps4",
    "xbox 360", "xbox one", "xbox one s", "xbox one x", "switch lite",
]

POSITIVE_CONSOLE_HINTS = [
    "konsola", "komplet", "zestaw", "sprzedam konsole", "sprzedam konsolę", "sprzedam ps5",
    "sprzedam xbox", "sprzedam switch", "z padem", "z kontrolerem", "z joy-conami",
    "w zestawie", "pełny zestaw", "pelny zestaw",
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


def _title_starts_with_accessory(title: str) -> bool:
    patterns = [
        r"^kierownica\b", r"^pad\b", r"^kontroler\b", r"^joy[- ]?con\b", r"^etui\b",
        r"^case\b", r"^dock\b", r"^gra\b", r"^filtr\b", r"^tv\b", r"^monitor\b",
    ]
    return any(re.search(pattern, title, re.IGNORECASE) for pattern in patterns)


def looks_like_accessory_or_part(offer: Offer) -> bool:
    title = _normalize(offer.title or "")
    desc = _normalize(offer.description or "")
    url = _normalize(offer.url or "")
    blob = f"{title} {desc} {url}".strip()

    if not offer.model:
        return True

    if _contains_any(blob, NON_CONSOLE_KEYWORDS):
        return True

    if _contains_any(blob, OLDER_OR_WRONG_CONSOLE_KEYWORDS):
        return True

    if _contains_any(title, PARTS_KEYWORDS) or _contains_any(desc, PARTS_KEYWORDS):
        return True

    if _contains_any(title, GAME_KEYWORDS):
        return True

    if _title_starts_with_accessory(title):
        return True

    if _contains_any(title, ACCESSORY_KEYWORDS):
        positive = _contains_any(title, ["konsola", "zestaw", "komplet"]) or _contains_any(desc, POSITIVE_CONSOLE_HINTS)
        if not positive:
            return True

    if offer.price and offer.price < 220:
        if _contains_any(blob, ACCESSORY_KEYWORDS + GAME_KEYWORDS + PARTS_KEYWORDS):
            return True

    accessory_only_patterns = [
        "do ps5", "do playstation 5", "do xbox series x", "do xbox series s", "do switch", "do steam deck",
        "for ps5", "for xbox", "for switch", "for steam deck",
    ]
    if any(p in title for p in accessory_only_patterns):
        return True

    if offer.model == "playstation 5" and ("portal" in blob or "remote player" in blob):
        return True

    return False


def offer_passes_basic_filters(offer: Offer, settings: Settings) -> bool:
    blob = _normalize(f"{offer.title} {offer.description} {offer.url}")

    parsed_title_model = parse_model(offer.title or "")
    if parsed_title_model and offer.model and parsed_title_model != offer.model:
        offer.model = parsed_title_model

    if looks_like_accessory_or_part(offer):
        return False

    if not offer.model:
        return False

    if settings.only_models_list and offer.model.lower() not in settings.only_models_list:
        return False

    if any(keyword in blob for keyword in settings.excluded_keywords_list):
        return False

    if offer.price < settings.MIN_PRICE:
        return False

    if offer.price > settings.MAX_PRICE:
        return False

    model_cap = settings.max_price_by_model.get(offer.model.lower())
    if model_cap is not None and offer.price > model_cap:
        return False

    return True
