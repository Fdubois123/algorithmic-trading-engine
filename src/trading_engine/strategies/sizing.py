from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from trading_engine.strategies.signals import (
    SignalDirection,
    StrategySignal,
)


def _validate_positive(
    value: float,
    *,
    name: str,
) -> None:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite.")

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")


class PositionSizer(ABC):
    """Interface for converting signals into target quantities."""

    @abstractmethod
    def size(
        self,
        *,
        signal: StrategySignal,
        equity: float,
        price: float,
    ) -> float:
        """Return signed target quantity."""
        raise NotImplementedError


@dataclass(slots=True, frozen=True)
class FixedFractionSizer(PositionSizer):
    """Allocate a fixed fraction of portfolio equity per signal."""

    fraction: float = 0.10

    def __post_init__(self) -> None:
        if isinstance(self.fraction, bool) or not isinstance(
            self.fraction,
            (int, float),
        ):
            raise TypeError("fraction must be numeric.")

        if not math.isfinite(float(self.fraction)):
            raise ValueError("fraction must be finite.")

        if not 0 < self.fraction <= 1:
            raise ValueError("fraction must be greater than 0 and at most 1.")

    def size(
        self,
        *,
        signal: StrategySignal,
        equity: float,
        price: float,
    ) -> float:
        _validate_positive(
            equity,
            name="equity",
        )

        _validate_positive(
            price,
            name="price",
        )

        if signal.direction is SignalDirection.FLAT:
            return 0.0

        capital = equity * self.fraction * signal.strength

        quantity = capital / price

        if signal.direction is SignalDirection.SHORT:
            quantity *= -1

        return float(quantity)


@dataclass(slots=True, frozen=True)
class VolatilityTargetSizer(PositionSizer):
    """Scale exposure according to forecast volatility.

    Exposure multiplier:

        target_volatility / forecast_volatility

    capped by max_leverage.
    """

    target_volatility: float = 0.10
    forecast_volatility: float = 0.20
    max_leverage: float = 1.0

    def __post_init__(self) -> None:
        for name, value in {
            "target_volatility": self.target_volatility,
            "forecast_volatility": self.forecast_volatility,
            "max_leverage": self.max_leverage,
        }.items():
            _validate_positive(
                value,
                name=name,
            )

    @property
    def exposure_multiplier(self) -> float:
        raw = self.target_volatility / self.forecast_volatility

        return float(min(raw, self.max_leverage))

    def size(
        self,
        *,
        signal: StrategySignal,
        equity: float,
        price: float,
    ) -> float:
        _validate_positive(
            equity,
            name="equity",
        )

        _validate_positive(
            price,
            name="price",
        )

        if signal.direction is SignalDirection.FLAT:
            return 0.0

        capital = equity * self.exposure_multiplier * signal.strength

        quantity = capital / price

        if signal.direction is SignalDirection.SHORT:
            quantity *= -1

        return float(quantity)
