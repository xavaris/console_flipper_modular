CONSOLE_MODELS = [
    "xbox series x",
    "xbox series s",
    "nintendo switch 2",
    "nintendo switch",
    "playstation 5",
    "steam deck",
]

MODEL_ALIASES = {
    "xbox series x": [
        "xbox series x",
        "xsx",
    ],
    "xbox series s": [
        "xbox series s",
        "xss",
        "x box series s",
    ],
    "nintendo switch 2": [
        "nintendo switch 2",
        "switch 2",
    ],
    "nintendo switch": [
        "nintendo switch",
        "switch oled",
        "switch v1",
        "switch v2",
        "switch hac",
    ],
    "playstation 5": [
        "playstation 5",
        "play station 5",
        "ps5",
    ],
    "steam deck": [
        "steam deck",
        "steamdeck",
    ],
}

STORAGE_PATTERNS = [
    "64gb", "128gb", "256gb", "512gb", "1tb",
]

COLOR_KEYWORDS = [
    "black", "white", "blue", "red", "gray", "grey", "silver",
    "czarny", "biały", "bialy", "niebieski", "czerwony", "szary", "srebrny",
]

CONDITION_KEYWORDS = {
    "jak nowa": ["jak nowa", "stan idealny", "idealny", "perfekcyjny", "bardzo zadbana"],
    "bardzo dobry": ["bardzo dobry", "super stan", "ładny stan", "ladny stan", "db+"],
    "dobry": ["dobry", "sprawna", "sprawny", "używana", "uzywana"],
    "uszkodzona": ["uszkodzona", "na części", "na czesci", "nie działa", "nie dziala"],
}

PLATFORM_NAMES = {
    "vinted": "Vinted",
    "olx": "OLX",
    "allegro_lokalnie": "Allegro Lokalnie",
}

SEARCH_TARGETS = {
    "allegro_lokalnie": {
        "xbox series x": "https://allegrolokalnie.pl/oferty/q/xbox%20series%20x?sort=startingTime-desc",
        "xbox series s": "https://allegrolokalnie.pl/oferty/q/xbox%20series%20s?sort=startingTime-desc",
        "nintendo switch": "https://allegrolokalnie.pl/oferty/q/nintendo%20switch?sort=startingTime-desc",
        "nintendo switch 2": "https://allegrolokalnie.pl/oferty/q/nintendo%20switch%202?sort=startingTime-desc",
        "playstation 5": "https://allegrolokalnie.pl/oferty/q/playstation%205?sort=startingTime-desc",
        "steam deck": "https://allegrolokalnie.pl/oferty/q/steam%20deck?sort=startingTime-desc",
    },
    "olx": {
        "xbox series s": "https://www.olx.pl/oferty/q-xbox-series-s/?search%5Border%5D=created_at:desc",
        "xbox series x": "https://www.olx.pl/oferty/q-xbox-series-x/?search%5Border%5D=created_at:desc",
        "nintendo switch": "https://www.olx.pl/oferty/q-nintendo-switch/?search%5Border%5D=created_at:desc",
        "nintendo switch 2": "https://www.olx.pl/oferty/q-nintendo-switch-2/?search%5Border%5D=created_at:desc",
        "playstation 5": "https://www.olx.pl/oferty/q-playstation-5/?search%5Border%5D=created_at:desc",
        "steam deck": "https://www.olx.pl/oferty/q-steam-deck/?search%5Border%5D=created_at:desc",
    },
    "vinted": {
        "xbox series s": "https://www.vinted.pl/catalog?search_text=xbox%20series%20s&order=newest_first&page=1&time={timestamp}",
        "xbox series x": "https://www.vinted.pl/catalog?search_text=xbox%20series%20x&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "nintendo switch": "https://www.vinted.pl/catalog?search_text=nintendo%20switch&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "nintendo switch 2": "https://www.vinted.pl/catalog?search_text=nintendo%20switch%202&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "playstation 5": "https://www.vinted.pl/catalog?search_text=playstation%205&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
        "steam deck": "https://www.vinted.pl/catalog?search_text=steam%20deck&order=newest_first&page=1&time={timestamp}&search_by_image_uuid=&search_by_image_id=",
    },
}
