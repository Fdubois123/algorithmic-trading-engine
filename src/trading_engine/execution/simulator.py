from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
)
from trading_engine.execution.commissions import (
    CommissionModel,
    NoCommission,
)
from trading_engine.execution.impact import (
    SquareRootMarketImpact,
)
from trading_engine.execution.liquidity import (
    ParticipationRateModel,
)
from trading_engine.execution.slippage import (
    BidAskSpreadModel,
    NoSlippage,
    SlippageModel,
)


@dataclass(slots=True, frozen=True)
class ExecutionResult:
    """Outcome of attempting to execute an order."""

    fill: Fill | None
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    status: OrderStatus

    @property
    def fill_fraction(self) -> float:
        if self.requested_quantity == 0:
            return 0.0

        return float(self.filled_quantity / self.requested_quantity)


class AdvancedExecutionSimulator:
    """Execution simulator with spread, costs, impact and liquidity."""

    def __init__(
        self,
        *,
        commission_model: CommissionModel | None = None,
        slippage_model: SlippageModel | None = None,
        spread_model: BidAskSpreadModel | None = None,
        liquidity_model: ParticipationRateModel | None = None,
        impact_model: SquareRootMarketImpact | None = None,
    ) -> None:
        self.commission_model = (
            commission_model if commission_model is not None else NoCommission()
        )

        self.slippage_model = (
            slippage_model if slippage_model is not None else NoSlippage()
        )

        self.spread_model = (
            spread_model if spread_model is not None else BidAskSpreadModel()
        )

        self.liquidity_model = liquidity_model
        self.impact_model = impact_model

    @staticmethod
    def _validate_market_price(
        market_price: float,
    ) -> float:
        if isinstance(
            market_price,
            bool,
        ) or not isinstance(
            market_price,
            (int, float),
        ):
            raise TypeError("market_price must be numeric.")

        if not math.isfinite(float(market_price)):
            raise ValueError("market_price must be finite.")

        if market_price <= 0:
            raise ValueError("market_price must be greater than zero.")

        return float(market_price)

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware.")

    @staticmethod
    def _limit_is_reachable(
        order: Order,
        market_price: float,
    ) -> bool:
        if order.order_type is OrderType.MARKET:
            return True

        if order.side is OrderSide.BUY:
            return market_price <= order.limit_price

        return market_price >= order.limit_price

    def execute(
        self,
        *,
        order: Order,
        market_price: float,
        timestamp: datetime,
        volume: float | None = None,
    ) -> ExecutionResult:
        market_price = self._validate_market_price(market_price)
        self._validate_timestamp(timestamp)

        requested_quantity = float(order.quantity)

        if not self._limit_is_reachable(
            order,
            market_price,
        ):
            return ExecutionResult(
                fill=None,
                requested_quantity=requested_quantity,
                filled_quantity=0.0,
                remaining_quantity=requested_quantity,
                status=order.status,
            )

        if self.liquidity_model is not None:
            if volume is None:
                raise ValueError(
                    "volume is required when a liquidity model is configured."
                )

            filled_quantity = self.liquidity_model.executable_quantity(
                requested_quantity=requested_quantity,
                volume=volume,
            )

        else:
            filled_quantity = requested_quantity

        if filled_quantity <= 0:
            return ExecutionResult(
                fill=None,
                requested_quantity=requested_quantity,
                filled_quantity=0.0,
                remaining_quantity=requested_quantity,
                status=order.status,
            )

        execution_price = self.spread_model.adjust(
            market_price=market_price,
            side=order.side,
        )

        execution_price = self.slippage_model.adjust(
            market_price=execution_price,
            side=order.side,
        )

        if self.impact_model is not None:
            if volume is None:
                raise ValueError(
                    "volume is required when a market-impact model is configured."
                )

            execution_price = self.impact_model.adjust(
                market_price=execution_price,
                side=order.side,
                quantity=filled_quantity,
                volume=volume,
            )

        if order.order_type is OrderType.LIMIT:
            if order.side is OrderSide.BUY and execution_price > order.limit_price:
                return ExecutionResult(
                    fill=None,
                    requested_quantity=requested_quantity,
                    filled_quantity=0.0,
                    remaining_quantity=requested_quantity,
                    status=order.status,
                )

            if order.side is OrderSide.SELL and execution_price < order.limit_price:
                return ExecutionResult(
                    fill=None,
                    requested_quantity=requested_quantity,
                    filled_quantity=0.0,
                    remaining_quantity=requested_quantity,
                    status=order.status,
                )

        commission = self.commission_model.calculate(
            quantity=filled_quantity,
            price=execution_price,
        )

        execution_friction = abs(execution_price - market_price) * filled_quantity

        remaining_quantity = max(
            requested_quantity - filled_quantity,
            0.0,
        )

        if remaining_quantity > 0:
            status = OrderStatus.PARTIALLY_FILLED
        else:
            status = OrderStatus.FILLED

        order.status = status

        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=filled_quantity,
            price=execution_price,
            commission=commission,
            slippage_cost=execution_friction,
            timestamp=timestamp,
        )

        return ExecutionResult(
            fill=fill,
            requested_quantity=requested_quantity,
            filled_quantity=filled_quantity,
            remaining_quantity=remaining_quantity,
            status=status,
        )
