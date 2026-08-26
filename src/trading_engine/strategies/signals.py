from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SignalDirection(str, Enum):
    """Desired directional exposure."""

    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


def _validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string.")

    normalized = symbol.strip().upper()

    if not normalized:
        raise ValueError("symbol cannot be empty.")

    return normalized


def _validate_finite_number(
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


@dataclass(slots=True, frozen=True)
class StrategySignal:
    """Signal produced by a quantitative strategy.

    Strength is normalized to [0, 1] and represents conviction,
    not position quantity.
    """

    symbol: str
    direction: SignalDirection
    timestamp: datetime
    strength: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "symbol",
            _validate_symbol(self.symbol),
        )

        if not isinstance(
            self.direction,
            SignalDirection,
        ):
            raise TypeError("direction must be a SignalDirection.")

        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")

        _validate_finite_number(
            self.strength,
            name="strength",
        )

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0 and 1.")

    @property
    def signed_strength(self) -> float:
        """Return direction-adjusted conviction."""
        if self.direction is SignalDirection.LONG:
            return self.strength

        if self.direction is SignalDirection.SHORT:
            return -self.strength

        return 0.0
