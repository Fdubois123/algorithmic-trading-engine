from __future__ import annotations

import math
from dataclasses import dataclass

from trading_engine.stat_arb.strategy import (
    PairPosition,
)


@dataclass(slots=True, frozen=True)
class PairLegWeights:
    """Capital weights for the two legs of a pair."""

    dependent: float
    independent: float

    @property
    def gross_exposure(self) -> float:
        return abs(self.dependent) + abs(self.independent)

    @property
    def net_exposure(self) -> float:
        return self.dependent + self.independent


def pair_leg_weights(
    *,
    hedge_ratio: float,
    position: PairPosition,
    gross_exposure: float = 1.0,
) -> PairLegWeights:
    """Convert a hedge ratio and pair state into two-leg weights."""
    if isinstance(hedge_ratio, bool) or not isinstance(
        hedge_ratio,
        (int, float),
    ):
        raise TypeError("hedge_ratio must be numeric.")

    hedge_ratio = float(hedge_ratio)

    if not math.isfinite(hedge_ratio):
        raise ValueError("hedge_ratio must be finite.")

    if hedge_ratio <= 0:
        raise ValueError("hedge_ratio must be greater than zero.")

    if not isinstance(
        position,
        PairPosition,
    ):
        raise TypeError("position must be a PairPosition.")

    if isinstance(
        gross_exposure,
        bool,
    ) or not isinstance(
        gross_exposure,
        (int, float),
    ):
        raise TypeError("gross_exposure must be numeric.")

    gross_exposure = float(gross_exposure)

    if not math.isfinite(gross_exposure):
        raise ValueError("gross_exposure must be finite.")

    if gross_exposure < 0:
        raise ValueError("gross_exposure cannot be negative.")

    if position is PairPosition.FLAT or gross_exposure == 0:
        return PairLegWeights(
            dependent=0.0,
            independent=0.0,
        )

    normalizer = 1.0 + hedge_ratio

    dependent_weight = gross_exposure / normalizer

    independent_weight = gross_exposure * hedge_ratio / normalizer

    if position is PairPosition.LONG_SPREAD:
        return PairLegWeights(
            dependent=dependent_weight,
            independent=-independent_weight,
        )

    return PairLegWeights(
        dependent=-dependent_weight,
        independent=independent_weight,
    )


def pair_share_quantities(
    *,
    capital: float,
    dependent_price: float,
    independent_price: float,
    hedge_ratio: float,
    position: PairPosition,
    gross_exposure: float = 1.0,
) -> tuple[float, float]:
    """Convert pair leg weights into fractional share quantities."""
    for name, value in {
        "capital": capital,
        "dependent_price": dependent_price,
        "independent_price": independent_price,
    }.items():
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(f"{name} must be numeric.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")

    capital = float(capital)
    dependent_price = float(dependent_price)
    independent_price = float(independent_price)

    if capital < 0:
        raise ValueError("capital cannot be negative.")

    if dependent_price <= 0:
        raise ValueError("dependent_price must be greater than zero.")

    if independent_price <= 0:
        raise ValueError("independent_price must be greater than zero.")

    weights = pair_leg_weights(
        hedge_ratio=hedge_ratio,
        position=position,
        gross_exposure=gross_exposure,
    )

    dependent_quantity = capital * weights.dependent / dependent_price

    independent_quantity = capital * weights.independent / independent_price

    return (
        float(dependent_quantity),
        float(independent_quantity),
    )
