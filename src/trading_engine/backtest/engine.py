from __future__ import annotations

from collections import deque
from collections.abc import Mapping

import pandas as pd

from trading_engine.backtest.events import (
    FillEvent,
    MarketEvent,
    OrderEvent,
    SignalEvent,
)
from trading_engine.backtest.execution import (
    ExecutionModel,
)
from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderStatus,
)
from trading_engine.backtest.portfolio import (
    Portfolio,
)
from trading_engine.backtest.results import (
    BacktestResult,
)
from trading_engine.backtest.strategy import (
    Strategy,
)


class BacktestEngine:
    """Event-driven historical backtesting engine."""

    def __init__(
        self,
        *,
        market_data: Mapping[str, pd.DataFrame],
        strategy: Strategy,
        portfolio: Portfolio,
        execution_model: ExecutionModel,
        periods_per_year: int = 252,
    ) -> None:
        if not market_data:
            raise ValueError("market_data cannot be empty.")

        self.market_data = {
            symbol.strip().upper(): frame for symbol, frame in market_data.items()
        }

        self.strategy = strategy
        self.portfolio = portfolio
        self.execution_model = execution_model
        self.periods_per_year = periods_per_year

        self.fills: list[Fill] = []
        self.orders: list[Order] = []

        self._validate_market_data()

    def _validate_market_data(self) -> None:
        for symbol, frame in self.market_data.items():
            if frame.empty:
                raise ValueError(f"Market data for {symbol} is empty.")

            if "close" not in frame.columns:
                raise ValueError(
                    f"Market data for {symbol} must contain a close column."
                )

            if not isinstance(
                frame.index,
                pd.DatetimeIndex,
            ):
                raise TypeError(f"Market data for {symbol} must use a DatetimeIndex.")

            if frame.index.has_duplicates:
                raise ValueError(
                    f"Market data for {symbol} contains duplicate timestamps."
                )

            if not frame.index.is_monotonic_increasing:
                raise ValueError(
                    f"Market data for {symbol} must be sorted chronologically."
                )

            if frame["close"].isna().any():
                raise ValueError(
                    f"Market data for {symbol} contains missing close prices."
                )

            if (frame["close"] <= 0).any():
                raise ValueError(
                    f"Market data for {symbol} contains non-positive close prices."
                )

    def _common_index(self) -> pd.DatetimeIndex:
        indexes = [frame.index for frame in self.market_data.values()]

        common = indexes[0]

        for index in indexes[1:]:
            common = common.intersection(index)

        if common.empty:
            raise ValueError("Market data has no common timestamps.")

        return common.sort_values()

    def run(self) -> BacktestResult:
        queue: deque[MarketEvent | SignalEvent | OrderEvent | FillEvent] = deque()

        for timestamp in self._common_index():
            prices = {
                symbol: float(frame.loc[timestamp, "close"])
                for symbol, frame in self.market_data.items()
            }

            queue.append(
                MarketEvent(
                    timestamp=timestamp.to_pydatetime(),
                    prices=prices,
                )
            )

            while queue:
                event = queue.popleft()

                if isinstance(event, MarketEvent):
                    self.portfolio.mark_to_market(event.prices)

                    signals = self.strategy.on_market(
                        event,
                        self.portfolio,
                    )

                    for signal in signals:
                        queue.append(signal)

                elif isinstance(event, SignalEvent):
                    order = Order(
                        symbol=event.symbol,
                        side=event.side,
                        quantity=event.quantity,
                        timestamp=event.timestamp,
                    )

                    order.status = OrderStatus.SUBMITTED

                    self.orders.append(order)

                    queue.append(OrderEvent(order))

                elif isinstance(event, OrderEvent):
                    order = event.order
                    market_price = prices[order.symbol]

                    try:
                        self.portfolio.validate_order(
                            order,
                            market_price,
                        )
                    except ValueError:
                        order.status = OrderStatus.REJECTED
                        continue

                    fill = self.execution_model.execute(
                        order,
                        market_price,
                        timestamp.to_pydatetime(),
                    )

                    if fill is not None:
                        queue.append(FillEvent(fill))

                elif isinstance(event, FillEvent):
                    self.portfolio.process_fill(event.fill)

                    self.fills.append(event.fill)

            self.portfolio.mark_to_market(prices)

            self.portfolio.record_equity(timestamp.to_pydatetime())

        equity_curve = pd.Series(
            {timestamp: equity for timestamp, equity in self.portfolio.equity_history},
            name="equity",
        )

        return BacktestResult(
            equity_curve=equity_curve,
            fills=tuple(self.fills),
            periods_per_year=self.periods_per_year,
        )
