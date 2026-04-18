from __future__ import annotations

import re

from app.config import Settings
from app.models import Offer

ACCESSORY_KEYWORDS = [
    "etui", "case", "pokrowiec", "obudowa", "skórka", "nakładka", "nakladka", "folia", "szkło",
    "szklo", "ładowarka", "ladowarka", "zasilacz", "kabel", "adapter", "uchwyt", "stojak",
    "stacja dokująca", "stacja dokujaca", "dock", "dok", "base", "uchwyt", "pokrywa",
    "pad", "pady", "kontroler", "kontrolery", "controller", "joy-con", "joy con", "joycon",
    "dualsense", "gamepad", "sluchawki", "słuchawki", "mikrofon", "kamera", "kamerka",
    "pudełko", "pudelko", "karton", "box", "sam box", "samo pudełko", "sam karton",
]

GAME_KEYWORDS = [
    "gra", "gry", "game", "games", "fifa", "ea fc", "fortnite", "zelda", "mario", "spiderman",
    "god of war", "forza", "minecraft", "cyberpunk", "call of duty", "cod ", "gta", "pokemon",
]

PARTS_KEYWORDS = [
    "na części", "na czesci", "części", "czesci", "część", "czesc", "uszkodzona", "uszkodzony",
    "nie działa", "nie dziala", "do naprawy", "na części", "plyta", "płyta", "hdmi port",
    "port hdmi", "wentylator", "obudowa dolna", "taśma", "tasma", "matryca", "lcd",
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


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _word_boundary_contains(text: str, keyword: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


def looks_like_accessory_or_part(offer: Offer) -> bool:
    title = (offer.title or "").lower().strip()
    desc = (offer.description or "").lower().strip()
    blob = f"{title} {desc}".strip()

    if not offer.model:
        return True

    if _contains_any(title, PARTS_KEYWORDS):
        return True

    if _contains_any(title, GAME_KEYWORDS):
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
    ]
    if any(p in title for p in accessory_only_patterns):
        return True

    return False


def offer_passes_basic_filters(offer: Offer, settings: Settings) -> bool:
    blob = f"{offer.title} {offer.description}".lower()

    if looks_like_accessory_or_part(offer):
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
