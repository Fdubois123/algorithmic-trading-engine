from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import datetime

from trading_engine.strategies.config import StrategyConfig
from trading_engine.strategies.signals import StrategySignal


def validate_strategy_symbol(symbol: str) -> str:
    """Validate and normalize a strategy symbol."""
    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string.")

    normalized = symbol.strip().upper()

    if not normalized:
        raise ValueError("symbol cannot be empty.")

    return normalized


def validate_market_price(price: float) -> float:
    """Validate a market price used by a strategy."""
    if isinstance(price, bool) or not isinstance(
        price,
        (int, float),
    ):
        raise TypeError("price must be numeric.")

    if not math.isfinite(float(price)):
        raise ValueError("price must be finite.")

    if price <= 0:
        raise ValueError("price must be greater than zero.")

    return float(price)


def validate_timestamp(
    timestamp: datetime,
) -> None:
    """Require timezone-aware strategy timestamps."""
    if not isinstance(timestamp, datetime):
        raise TypeError("timestamp must be a datetime.")

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware.")


def validate_positive_integer(
    value: int,
    *,
    name: str,
) -> None:
    """Validate a strictly positive integer."""
    if isinstance(value, bool) or not isinstance(
        value,
        int,
    ):
        raise TypeError(f"{name} must be an integer.")

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")


class QuantStrategy(ABC):
    """Base class for stateful quantitative signal models."""

    def __init__(
        self,
        *,
        symbol: str,
        config: StrategyConfig | None = None,
    ) -> None:
        self.symbol = validate_strategy_symbol(symbol)

        if config is None:
            config = StrategyConfig()

        if not isinstance(config, StrategyConfig):
            raise TypeError("config must be a StrategyConfig.")

        self.config = config

    @abstractmethod
    def update(
        self,
        *,
        price: float,
        timestamp: datetime,
    ) -> StrategySignal:
        """Consume a completed observation and return a signal."""
        raise NotImplementedError
