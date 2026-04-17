from __future__ import annotations

from .models import SearchTarget

TARGETS: list[SearchTarget] = [
    SearchTarget(
        key="switch",
        label="Nintendo Switch",
        emoji="🟥",
        aliases=[
            "Nintendo Switch",
            "Switch OLED",
            "Nintendo Switch OLED",
            "Switch Lite",
            "Nintendo Switch Lite",
        ],
        env_var="MAX_PRICE_SWITCH",
        default_max_price=1300,
    ),
    SearchTarget(
        key="steam_deck",
        label="Steam Deck",
        emoji="🚂",
        aliases=[
            "Steam Deck",
            "Steam Deck 64GB",
            "Steam Deck 256GB",
            "Steam Deck 512GB",
            "Steam Deck OLED",
            "Steam Deck LCD",
        ],
        env_var="MAX_PRICE_STEAM_DECK",
        default_max_price=1900,
    ),
    SearchTarget(
        key="ps5",
        label="PlayStation 5",
        emoji="🎮",
        aliases=[
            "PlayStation 5",
            "PS5",
            "PS5 Digital",
            "PS5 Slim",
            "PS5 Pro",
            "PS5 Standard",
        ],
        env_var="MAX_PRICE_PS5",
        default_max_price=2600,
    ),
    SearchTarget(
        key="xbox_series_x",
        label="Xbox Series X",
        emoji="🟩",
        aliases=[
            "Xbox Series X",
            "Xbox X",
            "Xbox Series X 1TB",
        ],
        env_var="MAX_PRICE_XBOX_SERIES_X",
        default_max_price=2300,
    ),
    SearchTarget(
        key="xbox_series_s",
        label="Xbox Series S",
        emoji="🟩",
        aliases=[
            "Xbox Series S",
            "Xbox S",
            "Xbox Series S 512GB",
            "Xbox Series S 1TB",
        ],
        env_var="MAX_PRICE_XBOX_SERIES_S",
        default_max_price=1600,
    ),
]

SOURCE_LABELS = {
    "vinted": "Vinted",
    "olx": "OLX",
    "allegro": "Allegro",
}
