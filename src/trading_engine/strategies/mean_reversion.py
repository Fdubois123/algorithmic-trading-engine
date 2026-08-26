from __future__ import annotations

import math
from collections import deque
from datetime import datetime

import numpy as np

from trading_engine.strategies.base import (
    QuantStrategy,
    validate_market_price,
    validate_positive_integer,
    validate_timestamp,
)
from trading_engine.strategies.config import StrategyConfig
from trading_engine.strategies.signals import (
    SignalDirection,
    StrategySignal,
)


class ZScoreMeanReversionStrategy(QuantStrategy):
    """Rolling z-score mean-reversion strategy."""

    def __init__(
        self,
        *,
        symbol: str,
        window: int = 20,
        entry_z: float = 2.0,
        exit_z: float = 0.5,
        config: StrategyConfig | None = None,
    ) -> None:
        super().__init__(
            symbol=symbol,
            config=config,
        )

        validate_positive_integer(
            window,
            name="window",
        )

        if window < 2:
            raise ValueError("window must be at least 2.")

        for name, value in {
            "entry_z": entry_z,
            "exit_z": exit_z,
        }.items():
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(f"{name} must be numeric.")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")

        if entry_z <= 0:
            raise ValueError("entry_z must be greater than zero.")

        if exit_z < 0:
            raise ValueError("exit_z cannot be negative.")

        if exit_z >= entry_z:
            raise ValueError("exit_z must be smaller than entry_z.")

        self.window = window
        self.entry_z = float(entry_z)
        self.exit_z = float(exit_z)

        self._prices: deque[float] = deque(maxlen=window)

        self._state = SignalDirection.FLAT

    @property
    def state(self) -> SignalDirection:
        """Return the current strategy state."""
        return self._state

    def update(
        self,
        *,
        price: float,
        timestamp: datetime,
    ) -> StrategySignal:
        """Consume a completed price observation and produce a signal."""
        price = validate_market_price(price)
        validate_timestamp(timestamp)

        self._prices.append(price)

        if len(self._prices) < self.window:
            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

        values = np.asarray(
            self._prices,
            dtype=float,
        )

        mean = float(values.mean())

        standard_deviation = float(values.std(ddof=1))

        if standard_deviation == 0:
            self._state = SignalDirection.FLAT

            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

        zscore = (price - mean) / standard_deviation

        if self._state is SignalDirection.FLAT:
            if zscore <= -self.entry_z:
                self._state = SignalDirection.LONG

            elif zscore >= self.entry_z and self.config.allow_short:
                self._state = SignalDirection.SHORT

        elif (self._state is SignalDirection.LONG and zscore >= -self.exit_z) or (
            self._state is SignalDirection.SHORT and zscore <= self.exit_z
        ):
            self._state = SignalDirection.FLAT

        strength = min(
            abs(zscore) / self.entry_z,
            1.0,
        )

        if self._state is SignalDirection.FLAT:
            strength = 0.0

        return StrategySignal(
            self.symbol,
            self._state,
            timestamp,
            strength=strength,
        )
