from __future__ import annotations

from ..models import Offer


class MarketBaselineService:
    """
    Hook for future baseline/median price analytics.
    The current bot publishes the lowest current listings and relies on max-price filters.
    """

    async def score_offer(self, offer: Offer) -> float:
        return float(offer.price)
