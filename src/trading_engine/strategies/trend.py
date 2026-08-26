from __future__ import annotations

from collections import deque
from datetime import datetime

import numpy as np

from trading_engine.strategies.base import (
    QuantStrategy,
    validate_market_price,
    validate_positive_integer,
    validate_timestamp,
)
from trading_engine.strategies.config import (
    StrategyConfig,
)
from trading_engine.strategies.signals import (
    SignalDirection,
    StrategySignal,
)


class MovingAverageTrendStrategy(QuantStrategy):
    """Fast/slow moving-average trend-following strategy."""

    def __init__(
        self,
        *,
        symbol: str,
        fast_window: int = 20,
        slow_window: int = 100,
        config: StrategyConfig | None = None,
    ) -> None:
        super().__init__(
            symbol=symbol,
            config=config,
        )

        validate_positive_integer(
            fast_window,
            name="fast_window",
        )
        validate_positive_integer(
            slow_window,
            name="slow_window",
        )

        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window.")

        self.fast_window = fast_window
        self.slow_window = slow_window

        self._prices: deque[float] = deque(maxlen=slow_window)

    def update(
        self,
        *,
        price: float,
        timestamp: datetime,
    ) -> StrategySignal:
        price = validate_market_price(price)
        validate_timestamp(timestamp)

        self._prices.append(price)

        if len(self._prices) < self.slow_window:
            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

        prices = np.asarray(
            self._prices,
            dtype=float,
        )

        fast_average = float(prices[-self.fast_window :].mean())
        slow_average = float(prices.mean())

        relative_gap = (fast_average - slow_average) / slow_average

        if abs(relative_gap) <= self.config.signal_threshold:
            direction = SignalDirection.FLAT

        elif relative_gap > 0:
            direction = SignalDirection.LONG

        elif self.config.allow_short:
            direction = SignalDirection.SHORT

        else:
            direction = SignalDirection.FLAT

        strength = min(
            abs(relative_gap),
            1.0,
        )

        if direction is SignalDirection.FLAT:
            strength = 0.0

        return StrategySignal(
            self.symbol,
            direction,
            timestamp,
            strength=strength,
        )
