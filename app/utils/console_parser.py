from __future__ import annotations

import re

from app.constants import (
    COLOR_KEYWORDS,
    CONDITION_KEYWORDS,
    MODEL_ALIASES,
    STORAGE_PATTERNS,
)
from app.utils.misc import clean_text


def parse_console_model(text: str) -> str:
    value = clean_text(text).lower()

    for canonical_model, aliases in MODEL_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if alias in value:
                return canonical_model

    return ""


def parse_console_storage(text: str) -> str:
    value = clean_text(text).lower().replace(" ", "")

    for item in STORAGE_PATTERNS:
        if item in value:
            return item.upper()

    match = re.search(r"\b(32|64|128|256|512)\s*gb\b", clean_text(text), re.IGNORECASE)
    if match:
        return f"{match.group(1)}GB"

    match = re.search(r"\b1\s*tb\b", clean_text(text), re.IGNORECASE)
    if match:
        return "1TB"

    return ""


def parse_console_color(text: str) -> str:
    value = clean_text(text).lower()
    for color in sorted(COLOR_KEYWORDS, key=len, reverse=True):
        if color in value:
            return color.title()
    return ""


def parse_console_condition(text: str) -> str:
    value = clean_text(text).lower()
    for label, keywords in CONDITION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in value:
                return label
    return ""


# Backward-compatible aliases for old imports across the project.
def parse_model(text: str) -> str:
    return parse_console_model(text)


def parse_storage(text: str) -> str:
    return parse_console_storage(text)


def parse_color(text: str) -> str:
    return parse_console_color(text)


def parse_condition(text: str) -> str:
    return parse_console_condition(text)
