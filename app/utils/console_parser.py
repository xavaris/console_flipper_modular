from __future__ import annotations

import re

from app.constants import COLOR_KEYWORDS, CONDITION_KEYWORDS, CONSOLE_MODELS, MODEL_ALIASES, STORAGE_PATTERNS
from app.utils.misc import clean_text


def parse_model(text: str) -> str:
    value = clean_text(text).lower()
    value = value.replace("sony ", "").replace("microsoft ", "")

    for model in CONSOLE_MODELS:
        aliases = MODEL_ALIASES.get(model, [])
        if any(alias in value for alias in aliases):
            return model

    if re.search(r"\bps5\b", value):
        return "playstation 5"

    if re.search(r"\bxsx\b", value):
        return "xbox series x"

    if re.search(r"\bxss\b", value):
        return "xbox series s"

    return ""


def parse_storage(text: str) -> str:
    value = clean_text(text).lower().replace(" ", "")
    for item in STORAGE_PATTERNS:
        if item in value:
            return item.upper()

    match = re.search(r"\b(64|128|256|512)\s*gb\b", value, re.IGNORECASE)
    if match:
        return f"{match.group(1)}GB"

    match = re.search(r"\b1\s*tb\b", value, re.IGNORECASE)
    if match:
        return "1TB"

    return ""


def parse_color(text: str) -> str:
    value = clean_text(text).lower()
    for color in sorted(COLOR_KEYWORDS, key=len, reverse=True):
        if color in value:
            return color.title()
    return ""


def parse_condition(text: str) -> str:
    value = clean_text(text).lower()
    for label, keywords in CONDITION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in value:
                return label
    return ""
