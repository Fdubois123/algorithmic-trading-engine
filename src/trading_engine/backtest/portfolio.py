from __future__ import annotations

import math
from datetime import datetime

from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderSide,
    Position,
)


class Portfolio:
    """Cash, positions and portfolio accounting."""

    def __init__(
        self,
        initial_cash: float,
        *,
        allow_short: bool = False,
        allow_margin: bool = False,
    ) -> None:
        if isinstance(initial_cash, bool) or not isinstance(
            initial_cash,
            (int, float),
        ):
            raise TypeError("initial_cash must be numeric.")

        if not math.isfinite(float(initial_cash)):
            raise ValueError("initial_cash must be finite.")

        if initial_cash <= 0:
            raise ValueError("initial_cash must be greater than zero.")

        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)

        self.allow_short = allow_short
        self.allow_margin = allow_margin

        self.positions: dict[str, Position] = {}

        self.equity_history: list[tuple[datetime, float]] = []

    def get_position(
        self,
        symbol: str,
    ) -> Position:
        symbol = symbol.strip().upper()

        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)

        return self.positions[symbol]

    def validate_order(
        self,
        order: Order,
        market_price: float,
    ) -> None:
        if market_price <= 0:
            raise ValueError("market_price must be greater than zero.")

        position = self.get_position(order.symbol)

        if (
            order.side is OrderSide.SELL
            and not self.allow_short
            and order.quantity > position.quantity
        ):
            raise ValueError("Order would create a short position.")

        estimated_notional = order.quantity * market_price

        if (
            order.side is OrderSide.BUY
            and not self.allow_margin
            and estimated_notional > self.cash
        ):
            raise ValueError("Insufficient cash for order.")

    def process_fill(
        self,
        fill: Fill,
    ) -> None:
        position = self.get_position(fill.symbol)

        position.apply_fill(fill)

        if fill.side is OrderSide.BUY:
            self.cash -= fill.notional + fill.execution_cost
        else:
            self.cash += fill.notional - fill.execution_cost

    def mark_to_market(
        self,
        prices: dict[str, float],
    ) -> None:
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].mark(price)

    @property
    def market_value(self) -> float:
        return float(sum(position.market_value for position in self.positions.values()))

    @property
    def equity(self) -> float:
        return float(self.cash + self.market_value)

    @property
    def gross_exposure(self) -> float:
        return float(
            sum(abs(position.market_value) for position in self.positions.values())
        )

    @property
    def net_exposure(self) -> float:
        return self.market_value

    def record_equity(
        self,
        timestamp: datetime,
    ) -> None:
        self.equity_history.append((timestamp, self.equity))
