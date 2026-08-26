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
from trading_engine.strategies.config import (
    StrategyConfig,
)
from trading_engine.strategies.signals import (
    SignalDirection,
    StrategySignal,
)


class VolatilityBreakoutStrategy(QuantStrategy):
    """Detect returns that exceed trailing volatility."""

    def __init__(
        self,
        *,
        symbol: str,
        lookback: int = 20,
        breakout_multiplier: float = 2.0,
        config: StrategyConfig | None = None,
    ) -> None:
        super().__init__(
            symbol=symbol,
            config=config,
        )

        validate_positive_integer(
            lookback,
            name="lookback",
        )

        if lookback < 2:
            raise ValueError("lookback must be at least 2.")

        if isinstance(
            breakout_multiplier,
            bool,
        ) or not isinstance(
            breakout_multiplier,
            (int, float),
        ):
            raise TypeError("breakout_multiplier must be numeric.")

        if not math.isfinite(float(breakout_multiplier)):
            raise ValueError("breakout_multiplier must be finite.")

        if breakout_multiplier <= 0:
            raise ValueError("breakout_multiplier must be greater than zero.")

        self.lookback = lookback
        self.breakout_multiplier = float(breakout_multiplier)

        self._returns: deque[float] = deque(maxlen=lookback)

        self._last_price: float | None = None

    def update(
        self,
        *,
        price: float,
        timestamp: datetime,
    ) -> StrategySignal:
        price = validate_market_price(price)
        validate_timestamp(timestamp)

        if self._last_price is None:
            self._last_price = price

            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

        current_return = (price / self._last_price) - 1.0

        self._last_price = price

        if len(self._returns) < self.lookback:
            self._returns.append(current_return)

            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

        previous_returns = np.asarray(
            self._returns,
            dtype=float,
        )

        forecast_volatility = float(previous_returns.std(ddof=1))

        volatility_threshold = forecast_volatility * self.breakout_multiplier

        threshold = max(
            volatility_threshold,
            self.config.signal_threshold,
        )

        if current_return > threshold:
            direction = SignalDirection.LONG

        elif current_return < -threshold and self.config.allow_short:
            direction = SignalDirection.SHORT

        else:
            direction = SignalDirection.FLAT

        self._returns.append(current_return)

        if direction is SignalDirection.FLAT:
            strength = 0.0
        elif threshold == 0:
            strength = 1.0
        else:
            strength = min(
                abs(current_return) / threshold,
                1.0,
            )

        return StrategySignal(
            self.symbol,
            direction,
            timestamp,
            strength=strength,
        )
