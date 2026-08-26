from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from trading_engine.regime.allocation import (
    RegimeAllocation,
    build_regime_allocation,
    normalize_strategy_weights,
    validate_strategy_weights,
)
from trading_engine.regime.labels import (
    MarketRegime,
)


@dataclass(slots=True, frozen=True)
class AdaptiveAllocationResult:
    """Final allocation after regime adaptation and turnover control."""

    regime: MarketRegime
    confidence: float
    weights: dict[str, float]
    gross_exposure: float
    cash_weight: float
    turnover: float

    @property
    def strategy_count(self) -> int:
        return len(self.weights)


def strategy_turnover(
    current_weights: Mapping[str, float],
    target_weights: Mapping[str, float],
) -> float:
    """Calculate one-way turnover between strategy allocations."""
    current = validate_strategy_weights(
        current_weights,
        require_positive_total=False,
    )

    target = validate_strategy_weights(
        target_weights,
        require_positive_total=False,
    )

    names = set(current) | set(target)

    return float(
        0.5 * sum(abs(target.get(name, 0.0) - current.get(name, 0.0)) for name in names)
    )


def apply_strategy_turnover_limit(
    current_weights: Mapping[str, float],
    target_weights: Mapping[str, float],
    *,
    maximum_turnover: float,
) -> dict[str, float]:
    """Move toward target allocation without exceeding turnover budget."""
    current = validate_strategy_weights(
        current_weights,
        require_positive_total=False,
    )

    target = validate_strategy_weights(
        target_weights,
        require_positive_total=False,
    )

    if isinstance(
        maximum_turnover,
        bool,
    ) or not isinstance(
        maximum_turnover,
        (int, float),
    ):
        raise TypeError("maximum_turnover must be numeric.")

    maximum_turnover = float(maximum_turnover)

    if not math.isfinite(maximum_turnover):
        raise ValueError("maximum_turnover must be finite.")

    if maximum_turnover < 0:
        raise ValueError("maximum_turnover cannot be negative.")

    turnover = strategy_turnover(
        current,
        target,
    )

    if turnover <= maximum_turnover:
        return dict(target)

    if maximum_turnover == 0:
        return dict(current)

    fraction = maximum_turnover / turnover

    names = set(current) | set(target)

    return {
        name: float(
            current.get(name, 0.0)
            + fraction * (target.get(name, 0.0) - current.get(name, 0.0))
        )
        for name in names
    }


def blend_with_base_allocation(
    regime_weights: Mapping[str, float],
    base_weights: Mapping[str, float],
    *,
    confidence: float,
) -> dict[str, float]:
    """Blend base strategy weights with regime-specific preferences."""
    regime_values = validate_strategy_weights(regime_weights)

    base_values = validate_strategy_weights(base_weights)

    if isinstance(
        confidence,
        bool,
    ) or not isinstance(
        confidence,
        (int, float),
    ):
        raise TypeError("confidence must be numeric.")

    confidence = float(confidence)

    if not math.isfinite(confidence):
        raise ValueError("confidence must be finite.")

    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1.")

    regime_normalized = normalize_strategy_weights(regime_values)

    base_normalized = normalize_strategy_weights(base_values)

    names = set(regime_normalized) | set(base_normalized)

    blended = {
        name: float(
            confidence
            * regime_normalized.get(
                name,
                0.0,
            )
            + (1.0 - confidence)
            * base_normalized.get(
                name,
                0.0,
            )
        )
        for name in names
    }

    return normalize_strategy_weights(blended)


class AdaptiveStrategyAllocator:
    """Regime-aware strategy allocation engine."""

    def __init__(
        self,
        *,
        base_weights: Mapping[str, float] | None = None,
        minimum_exposure: float = 0.25,
        maximum_exposure: float = 1.0,
        maximum_turnover: float = 0.25,
    ) -> None:
        if base_weights is None:
            base_weights = {
                "trend": 0.20,
                "momentum": 0.20,
                "mean_reversion": 0.20,
                "volatility": 0.20,
                "stat_arb": 0.20,
            }

        self.base_weights = normalize_strategy_weights(base_weights)

        if isinstance(
            minimum_exposure,
            bool,
        ) or not isinstance(
            minimum_exposure,
            (int, float),
        ):
            raise TypeError("minimum_exposure must be numeric.")

        if isinstance(
            maximum_exposure,
            bool,
        ) or not isinstance(
            maximum_exposure,
            (int, float),
        ):
            raise TypeError("maximum_exposure must be numeric.")

        self.minimum_exposure = float(minimum_exposure)

        self.maximum_exposure = float(maximum_exposure)

        if self.minimum_exposure < 0 or not math.isfinite(self.minimum_exposure):
            raise ValueError("minimum_exposure must be finite and non-negative.")

        if self.maximum_exposure <= 0 or not math.isfinite(self.maximum_exposure):
            raise ValueError("maximum_exposure must be finite and greater than zero.")

        if self.minimum_exposure > self.maximum_exposure:
            raise ValueError("minimum_exposure cannot exceed maximum_exposure.")

        if isinstance(
            maximum_turnover,
            bool,
        ) or not isinstance(
            maximum_turnover,
            (int, float),
        ):
            raise TypeError("maximum_turnover must be numeric.")

        self.maximum_turnover = float(maximum_turnover)

        if not math.isfinite(self.maximum_turnover) or self.maximum_turnover < 0:
            raise ValueError("maximum_turnover must be finite and non-negative.")

        self._current_weights = {name: 0.0 for name in self.base_weights}

    @property
    def current_weights(
        self,
    ) -> dict[str, float]:
        return dict(self._current_weights)

    def reset(
        self,
    ) -> None:
        """Reset current exposure to zero."""
        self._current_weights = {name: 0.0 for name in self.base_weights}

    def allocate(
        self,
        *,
        regime: MarketRegime,
        confidence: float,
    ) -> AdaptiveAllocationResult:
        """Calculate the next adaptive strategy allocation."""
        if not isinstance(
            regime,
            MarketRegime,
        ):
            raise TypeError("regime must be a MarketRegime.")

        if isinstance(
            confidence,
            bool,
        ) or not isinstance(
            confidence,
            (int, float),
        ):
            raise TypeError("confidence must be numeric.")

        confidence = float(confidence)

        if not math.isfinite(confidence):
            raise ValueError("confidence must be finite.")

        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1.")

        regime_allocation: RegimeAllocation = build_regime_allocation(
            regime,
            confidence=confidence,
            minimum_exposure=self.minimum_exposure,
            maximum_exposure=self.maximum_exposure,
        )

        regime_normalized = normalize_strategy_weights(regime_allocation.weights)

        blended = blend_with_base_allocation(
            regime_normalized,
            self.base_weights,
            confidence=confidence,
        )

        desired = {
            name: float(weight * regime_allocation.gross_exposure)
            for name, weight in blended.items()
        }

        limited = apply_strategy_turnover_limit(
            self._current_weights,
            desired,
            maximum_turnover=self.maximum_turnover,
        )

        turnover = strategy_turnover(
            self._current_weights,
            limited,
        )

        self._current_weights = dict(limited)

        gross_exposure = float(sum(abs(value) for value in limited.values()))

        cash_weight = float(
            max(
                1.0 - gross_exposure,
                0.0,
            )
        )

        return AdaptiveAllocationResult(
            regime=regime,
            confidence=confidence,
            weights=dict(limited),
            gross_exposure=gross_exposure,
            cash_weight=cash_weight,
            turnover=turnover,
        )
