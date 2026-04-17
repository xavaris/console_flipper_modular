from __future__ import annotations

from ..constants import TARGETS


def list_console_keys() -> list[str]:
    return [target.key for target in TARGETS]


def list_console_labels() -> dict[str, str]:
    return {target.key: target.label for target in TARGETS}
