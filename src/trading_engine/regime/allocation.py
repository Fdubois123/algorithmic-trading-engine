from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from trading_engine.regime.labels import (
    MarketRegime,
)

STRATEGY_NAMES = (
    "trend",
    "momentum",
    "mean_reversion",
    "volatility",
    "stat_arb",
)


@dataclass(slots=True, frozen=True)
class RegimeAllocation:
    """Strategy allocation for a market regime."""

    weights: dict[str, float]
    gross_exposure: float
    cash_weight: float

    @property
    def invested_weight(self) -> float:
        return float(sum(abs(value) for value in self.weights.values()))


def _validate_numeric(
    value: float,
    *,
    name: str,
    allow_zero: bool = True,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
    elif value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def validate_strategy_weights(
    weights: Mapping[str, float],
    *,
    require_positive_total: bool = True,
) -> dict[str, float]:
    """Validate a strategy-weight mapping."""
    if not isinstance(
        weights,
        Mapping,
    ):
        raise TypeError("weights must be a mapping.")

    if not weights:
        raise ValueError("weights cannot be empty.")

    result: dict[str, float] = {}

    for name, value in weights.items():
        if not isinstance(
            name,
            str,
        ):
            raise TypeError("strategy names must be strings.")

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError("strategy names cannot be empty.")

        numeric_value = _validate_numeric(
            value,
            name=normalized_name,
        )

        result[normalized_name] = numeric_value

    total = float(sum(result.values()))

    if require_positive_total and total <= 1e-15:
        raise ValueError("strategy weights must contain positive total exposure.")

    return result


def normalize_strategy_weights(
    weights: Mapping[str, float],
) -> dict[str, float]:
    """Normalize non-negative strategy weights to sum to one."""
    values = validate_strategy_weights(weights)

    total = float(sum(values.values()))

    return {name: float(value / total) for name, value in values.items()}


def regime_strategy_preferences(
    regime: MarketRegime,
) -> dict[str, float]:
    """Return heuristic strategy preferences for one market regime."""
    if not isinstance(
        regime,
        MarketRegime,
    ):
        raise TypeError("regime must be a MarketRegime.")

    preferences = {
        MarketRegime.LOW_VOL_BEAR: {
            "trend": 0.25,
            "momentum": 0.15,
            "mean_reversion": 0.25,
            "volatility": 0.10,
            "stat_arb": 0.25,
        },
        MarketRegime.LOW_VOL_SIDEWAYS: {
            "trend": 0.10,
            "momentum": 0.10,
            "mean_reversion": 0.35,
            "volatility": 0.10,
            "stat_arb": 0.35,
        },
        MarketRegime.LOW_VOL_BULL: {
            "trend": 0.30,
            "momentum": 0.30,
            "mean_reversion": 0.15,
            "volatility": 0.05,
            "stat_arb": 0.20,
        },
        MarketRegime.NORMAL_VOL_BEAR: {
            "trend": 0.30,
            "momentum": 0.15,
            "mean_reversion": 0.15,
            "volatility": 0.20,
            "stat_arb": 0.20,
        },
        MarketRegime.NORMAL_VOL_SIDEWAYS: {
            "trend": 0.15,
            "momentum": 0.10,
            "mean_reversion": 0.30,
            "volatility": 0.15,
            "stat_arb": 0.30,
        },
        MarketRegime.NORMAL_VOL_BULL: {
            "trend": 0.30,
            "momentum": 0.30,
            "mean_reversion": 0.10,
            "volatility": 0.10,
            "stat_arb": 0.20,
        },
        MarketRegime.HIGH_VOL_BEAR: {
            "trend": 0.25,
            "momentum": 0.10,
            "mean_reversion": 0.05,
            "volatility": 0.35,
            "stat_arb": 0.25,
        },
        MarketRegime.HIGH_VOL_SIDEWAYS: {
            "trend": 0.10,
            "momentum": 0.05,
            "mean_reversion": 0.20,
            "volatility": 0.35,
            "stat_arb": 0.30,
        },
        MarketRegime.HIGH_VOL_BULL: {
            "trend": 0.30,
            "momentum": 0.25,
            "mean_reversion": 0.05,
            "volatility": 0.20,
            "stat_arb": 0.20,
        },
    }

    return dict(preferences[regime])


def regime_gross_exposure(
    regime: MarketRegime,
    *,
    confidence: float = 1.0,
    minimum_exposure: float = 0.25,
    maximum_exposure: float = 1.0,
) -> float:
    """Determine gross exposure from regime risk and confidence."""
    if not isinstance(
        regime,
        MarketRegime,
    ):
        raise TypeError("regime must be a MarketRegime.")

    confidence = _validate_numeric(
        confidence,
        name="confidence",
    )

    if confidence > 1:
        raise ValueError("confidence must be at most 1.")

    minimum_exposure = _validate_numeric(
        minimum_exposure,
        name="minimum_exposure",
    )

    maximum_exposure = _validate_numeric(
        maximum_exposure,
        name="maximum_exposure",
        allow_zero=False,
    )

    if minimum_exposure > maximum_exposure:
        raise ValueError("minimum_exposure cannot exceed maximum_exposure.")

    if regime in {
        MarketRegime.HIGH_VOL_BEAR,
        MarketRegime.HIGH_VOL_SIDEWAYS,
    }:
        regime_multiplier = 0.45

    elif regime in {
        MarketRegime.HIGH_VOL_BULL,
        MarketRegime.NORMAL_VOL_BEAR,
    }:
        regime_multiplier = 0.70

    elif regime in {
        MarketRegime.LOW_VOL_SIDEWAYS,
        MarketRegime.NORMAL_VOL_SIDEWAYS,
    }:
        regime_multiplier = 0.80

    else:
        regime_multiplier = 1.0

    confidence_multiplier = 0.5 + 0.5 * confidence

    target = maximum_exposure * regime_multiplier * confidence_multiplier

    return float(
        np.clip(
            target,
            minimum_exposure,
            maximum_exposure,
        )
    )


def build_regime_allocation(
    regime: MarketRegime,
    *,
    confidence: float = 1.0,
    minimum_exposure: float = 0.25,
    maximum_exposure: float = 1.0,
) -> RegimeAllocation:
    """Construct normalized strategy allocation for a regime."""
    preferences = regime_strategy_preferences(regime)

    normalized = normalize_strategy_weights(preferences)

    gross_exposure = regime_gross_exposure(
        regime,
        confidence=confidence,
        minimum_exposure=minimum_exposure,
        maximum_exposure=maximum_exposure,
    )

    scaled = {
        name: float(weight * gross_exposure) for name, weight in normalized.items()
    }

    cash_weight = max(
        1.0 - gross_exposure,
        0.0,
    )

    return RegimeAllocation(
        weights=scaled,
        gross_exposure=gross_exposure,
        cash_weight=float(cash_weight),
    )
