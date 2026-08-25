from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from trading_engine.backtest.events import (
    MarketEvent,
    SignalEvent,
)
from trading_engine.backtest.portfolio import (
    Portfolio,
)


class Strategy(ABC):
    """Base interface for all trading strategies."""

    @abstractmethod
    def on_market(
        self,
        event: MarketEvent,
        portfolio: Portfolio,
    ) -> Iterable[SignalEvent]:
        """Generate trading signals from a market event."""
        raise NotImplementedError
