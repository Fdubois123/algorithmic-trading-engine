from __future__ import annotations

import math
from dataclasses import dataclass

from trading_engine.backtest.models import OrderSide


@dataclass(slots=True, frozen=True)
class SquareRootMarketImpact:
    """Square-root market-impact approximation.

    impact_bps =
        coefficient_bps * sqrt(participation_rate)

    The final value is capped by max_impact_bps.
    """

    coefficient_bps: float = 25.0
    max_impact_bps: float = 200.0

    def __post_init__(self) -> None:
        for name, value in {
            "coefficient_bps": self.coefficient_bps,
            "max_impact_bps": self.max_impact_bps,
        }.items():
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(f"{name} must be numeric.")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")

            if value < 0:
                raise ValueError(f"{name} cannot be negative.")

    def impact_bps(
        self,
        *,
        quantity: float,
        volume: float,
    ) -> float:
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero.")

        if volume <= 0:
            raise ValueError("volume must be greater than zero.")

        participation = quantity / volume

        raw = self.coefficient_bps * math.sqrt(participation)

        return float(
            min(
                raw,
                self.max_impact_bps,
            )
        )

    def adjust(
        self,
        *,
        market_price: float,
        side: OrderSide,
        quantity: float,
        volume: float,
    ) -> float:
        bps = self.impact_bps(
            quantity=quantity,
            volume=volume,
        )

        fraction = bps / 10_000.0

        if side is OrderSide.BUY:
            return float(market_price * (1.0 + fraction))

        return float(market_price * (1.0 - fraction))
