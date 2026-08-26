from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StrategyConfig:
    """Common risk and behavioural controls for quantitative strategies."""

    allow_short: bool = False

    max_position_weight: float = 1.0
    max_gross_exposure: float = 1.0

    signal_threshold: float = 0.0

    minimum_holding_period: int = 0
    cooldown_period: int = 0

    # Signals generated from bar t must execute on a future bar.
    signal_lag: int = 1

    def __post_init__(self) -> None:
        for name, value in {
            "max_position_weight": self.max_position_weight,
            "max_gross_exposure": self.max_gross_exposure,
            "signal_threshold": self.signal_threshold,
        }.items():
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(f"{name} must be numeric.")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")

        if not 0 < self.max_position_weight <= 1:
            raise ValueError(
                "max_position_weight must be greater than 0 and at most 1."
            )

        if self.max_gross_exposure <= 0:
            raise ValueError("max_gross_exposure must be greater than zero.")

        if not 0 <= self.signal_threshold <= 1:
            raise ValueError("signal_threshold must be between 0 and 1.")

        for name, value in {
            "minimum_holding_period": self.minimum_holding_period,
            "cooldown_period": self.cooldown_period,
            "signal_lag": self.signal_lag,
        }.items():
            if isinstance(value, bool) or not isinstance(
                value,
                int,
            ):
                raise TypeError(f"{name} must be an integer.")

            if value < 0:
                raise ValueError(f"{name} cannot be negative.")

        if self.signal_lag < 1:
            raise ValueError(
                "signal_lag must be at least 1 to prevent same-bar execution."
            )
