from __future__ import annotations

from collections import deque
from datetime import datetime

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


class TimeSeriesMomentumStrategy(QuantStrategy):
    """Directional strategy based on trailing price momentum."""

    def __init__(
        self,
        *,
        symbol: str,
        lookback: int = 20,
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

        self.lookback = lookback

        self._prices: deque[float] = deque(maxlen=lookback + 1)

    def update(
        self,
        *,
        price: float,
        timestamp: datetime,
    ) -> StrategySignal:
        price = validate_market_price(price)
        validate_timestamp(timestamp)

        self._prices.append(price)

        if len(self._prices) < self.lookback + 1:
            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

        starting_price = self._prices[0]

        momentum = (price / starting_price) - 1.0

        threshold = self.config.signal_threshold

        if momentum > threshold:
            direction = SignalDirection.LONG

        elif momentum < -threshold and self.config.allow_short:
            direction = SignalDirection.SHORT

        else:
            direction = SignalDirection.FLAT

        strength = min(
            abs(momentum),
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
