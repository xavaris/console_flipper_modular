from __future__ import annotations

import html

from ..constants import SOURCE_LABELS
from ..models import Offer, SearchTarget


def build_offer_caption(target: SearchTarget, offer: Offer) -> str:
    source_label = SOURCE_LABELS.get(offer.source, offer.source.title())
    lines = [
        f"{target.emoji} <b>{html.escape(offer.title)}</b>",
        f"💰 <b>{offer.price} zł</b>",
        f"📍 {html.escape(offer.location or 'Polska')}",
        f"🏪 {html.escape(source_label)}",
        f"🔗 {html.escape(offer.url)}",
    ]
    return "\n".join(lines)
