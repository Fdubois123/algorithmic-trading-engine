from __future__ import annotations

import math
from datetime import datetime

from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
)


class ExecutionModel:
    """Simple deterministic execution simulator."""

    def __init__(
        self,
        *,
        commission_rate: float = 0.0,
        fixed_commission: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> None:
        for name, value in {
            "commission_rate": commission_rate,
            "fixed_commission": fixed_commission,
            "slippage_bps": slippage_bps,
        }.items():
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(f"{name} must be numeric.")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")

            if value < 0:
                raise ValueError(f"{name} cannot be negative.")

        self.commission_rate = float(commission_rate)
        self.fixed_commission = float(fixed_commission)
        self.slippage_bps = float(slippage_bps)

    def execute(
        self,
        order: Order,
        market_price: float,
        timestamp: datetime,
    ) -> Fill | None:
        if market_price <= 0:
            raise ValueError("market_price must be greater than zero.")

        if order.order_type is OrderType.LIMIT:
            if order.side is OrderSide.BUY and market_price > order.limit_price:
                return None

            if order.side is OrderSide.SELL and market_price < order.limit_price:
                return None

        slippage_fraction = self.slippage_bps / 10_000.0

        if order.side is OrderSide.BUY:
            execution_price = market_price * (1.0 + slippage_fraction)
        else:
            execution_price = market_price * (1.0 - slippage_fraction)

        notional = order.quantity * execution_price

        commission = self.fixed_commission + notional * self.commission_rate

        slippage_cost = abs(execution_price - market_price) * order.quantity

        order.status = OrderStatus.FILLED

        return Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            commission=commission,
            slippage_cost=slippage_cost,
            timestamp=timestamp,
        )
