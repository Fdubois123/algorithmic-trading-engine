from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ResearchConfig:
    """Configuration for one reproducible research experiment."""

    volatility_window: int = 20
    trend_window: int = 50
    momentum_lookback: int = 20

    low_volatility_quantile: float = 0.25
    high_volatility_quantile: float = 0.75
    trend_threshold: float = 0.001
    momentum_threshold: float = 0.02

    minimum_exposure: float = 0.25
    maximum_exposure: float = 1.0
    maximum_turnover: float = 0.25

    transaction_cost_bps: float = 0.0

    base_weights: Mapping[str, float] | None = field(default=None)

    def __post_init__(self) -> None:
        for name in (
            "volatility_window",
            "trend_window",
            "momentum_lookback",
        ):
            value = getattr(
                self,
                name,
            )

            if isinstance(
                value,
                bool,
            ) or not isinstance(
                value,
                int,
            ):
                raise TypeError(f"{name} must be an integer.")

            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")

        if self.volatility_window < 2:
            raise ValueError("volatility_window must be at least 2.")

        if self.trend_window < 2:
            raise ValueError("trend_window must be at least 2.")

        numeric_values = {
            "low_volatility_quantile": (self.low_volatility_quantile),
            "high_volatility_quantile": (self.high_volatility_quantile),
            "trend_threshold": self.trend_threshold,
            "momentum_threshold": self.momentum_threshold,
            "minimum_exposure": self.minimum_exposure,
            "maximum_exposure": self.maximum_exposure,
            "maximum_turnover": self.maximum_turnover,
            "transaction_cost_bps": self.transaction_cost_bps,
        }

        for name, value in numeric_values.items():
            if isinstance(
                value,
                bool,
            ) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(f"{name} must be numeric.")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")

        if not (0 < self.low_volatility_quantile < self.high_volatility_quantile < 1):
            raise ValueError("volatility quantiles must satisfy 0 < low < high < 1.")

        if self.trend_threshold < 0:
            raise ValueError("trend_threshold cannot be negative.")

        if self.momentum_threshold < 0:
            raise ValueError("momentum_threshold cannot be negative.")

        if self.minimum_exposure < 0:
            raise ValueError("minimum_exposure cannot be negative.")

        if self.maximum_exposure <= 0:
            raise ValueError("maximum_exposure must be greater than zero.")

        if self.minimum_exposure > self.maximum_exposure:
            raise ValueError("minimum_exposure cannot exceed maximum_exposure.")

        if self.maximum_turnover < 0:
            raise ValueError("maximum_turnover cannot be negative.")

        if self.transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps cannot be negative.")
