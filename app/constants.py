from __future__ import annotations

CONSOLE_MODELS = [
    "playstation portal",
    "playstation 5",
    "xbox series x",
    "xbox series s",
    "nintendo switch 2",
    "nintendo switch",
    "steam deck",
]

MODEL_ALIASES = {
    "playstation portal": [
        "playstation portal",
        "ps portal",
        "portal ps5",
        "playstation portal remote player",
    ],
    "playstation 5": [
        "playstation 5",
        "ps5",
        "ps 5",
        "sony playstation 5",
    ],
    "xbox series x": [
        "xbox series x",
    ],
    "xbox series s": [
        "xbox series s",
    ],
    "nintendo switch 2": [
        "nintendo switch 2",
        "switch 2",
    ],
    "nintendo switch": [
        "nintendo switch",
        "switch oled",
        "nintendo switch oled",
        "switch v2",
        "switch hac-001",
    ],
    "steam deck": [
        "steam deck",
        "steamdeck",
    ],
}

STORAGE_PATTERNS = [
    "32gb",
    "64gb",
    "128gb",
    "256gb",
    "512gb",
    "1tb",
]

COLOR_KEYWORDS = [
    "black",
    "white",
    "blue",
    "red",
    "gray",
    "grey",
    "silver",
    "czarny",
    "biały",
    "bialy",
    "niebieski",
    "czerwony",
    "szary",
    "srebrny",
    "grafitowy",
]

CONDITION_KEYWORDS = {
    "jak nowy": [
        "jak nowy",
        "idealny",
        "stan idealny",
        "perfekcyjny",
        "nowy",
    ],
    "bardzo dobry": [
        "bardzo dobry",
        "super stan",
        "ładny stan",
        "ladny stan",
    ],
    "dobry": [
        "dobry",
        "sprawny",
        "używany",
        "uzywany",
    ],
    "uszkodzony": [
        "uszkodzony",
        "na części",
        "na czesci",
        "nie działa",
        "nie dziala",
    ],
}

PLATFORM_NAMES = {
    "vinted": "Vinted",
    "olx": "OLX",
    "allegro_lokalnie": "Allegro Lokalnie",
}

CONSOLE_SEARCH_URLS = {
    "allegro_lokalnie": {
        "xbox series x": "https://allegrolokalnie.pl/oferty/q/xbox%20series%20x?sort=startingTime-desc",
        "xbox series s": "https://allegrolokalnie.pl/oferty/q/xbox%20series%20s?sort=startingTime-desc",
        "nintendo switch": "https://allegrolokalnie.pl/oferty/q/nintendo%20switch?sort=startingTime-desc",
        "nintendo switch 2": "https://allegrolokalnie.pl/oferty/q/nintendo%20switch%202?sort=startingTime-desc",
        "playstation 5": "https://allegrolokalnie.pl/oferty/q/playstation%205?sort=startingTime-desc",
        "steam deck": "https://allegrolokalnie.pl/oferty/q/steam%20deck?sort=startingTime-desc",
        "playstation portal": "https://allegrolokalnie.pl/oferty/q/playstation%20portal?sort=startingTime-desc",
    },
    "olx": {
        "xbox series s": "https://www.olx.pl/oferty/q-xbox-series-s/?search%5Border%5D=created_at:desc",
        "xbox series x": "https://www.olx.pl/oferty/q-xbox-series-x/?search%5Border%5D=created_at:desc",
        "nintendo switch": "https://www.olx.pl/oferty/q-nintendo-switch/?search%5Border%5D=created_at:desc",
        "nintendo switch 2": "https://www.olx.pl/oferty/q-nintendo-switch-2/?search%5Border%5D=created_at:desc",
        "playstation 5": "https://www.olx.pl/oferty/q-playstation-5/?search%5Border%5D=created_at:desc",
        "steam deck": "https://www.olx.pl/oferty/q-steam-deck/?search%5Border%5D=created_at:desc",
        "playstation portal": "https://www.olx.pl/oferty/q-playstation-portal/?search%5Border%5D=created_at:desc",
    },
    "vinted": {
        "xbox series s": "https://www.vinted.pl/catalog?search_text=xbox%20series%20s&order=newest_first&page=1&time={timestamp}",
        "xbox series x": "https://www.vinted.pl/catalog?search_text=xbox%20series%20x&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "nintendo switch": "https://www.vinted.pl/catalog?search_text=nintendo%20switch&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "nintendo switch 2": "https://www.vinted.pl/catalog?search_text=nintendo%20switch%202&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "playstation 5": "https://www.vinted.pl/catalog?search_text=playstation%205&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "steam deck": "https://www.vinted.pl/catalog?search_text=steam%20deck&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "playstation portal": "https://www.vinted.pl/catalog?search_text=playstation%20portal&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
    },
}
