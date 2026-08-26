from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderSide,
    OrderStatus,
)
from trading_engine.backtest.portfolio import Portfolio
from trading_engine.backtest.results import BacktestResult
from trading_engine.execution import (
    AdvancedExecutionSimulator,
    ExecutionResult,
)
from trading_engine.strategies import (
    PositionSizer,
    QuantStrategy,
    SignalDirection,
    StrategySignal,
)


@dataclass(slots=True, frozen=True)
class PendingSignal:
    """Strategy signal waiting for a future execution bar."""

    signal: StrategySignal
    execution_bar: int


class QuantBacktestEngine:
    """Quantitative backtest engine with delayed realistic execution.

    Bar processing order:

    1. Mark current positions to the new market price.
    2. Execute signals generated on previous bars.
    3. Apply resulting fills to the portfolio.
    4. Generate today's strategy signal.
    5. Schedule today's signal for a future bar.
    6. Record end-of-bar portfolio equity.

    This prevents a strategy from observing a bar and then executing
    against the same bar price.
    """

    def __init__(
        self,
        *,
        market_data: pd.DataFrame,
        strategy: QuantStrategy,
        position_sizer: PositionSizer,
        portfolio: Portfolio,
        execution_simulator: AdvancedExecutionSimulator,
        periods_per_year: int = 252,
    ) -> None:
        if not isinstance(market_data, pd.DataFrame):
            raise TypeError("market_data must be a pandas DataFrame.")

        if not isinstance(strategy, QuantStrategy):
            raise TypeError("strategy must be a QuantStrategy.")

        if not isinstance(position_sizer, PositionSizer):
            raise TypeError("position_sizer must be a PositionSizer.")

        if not isinstance(portfolio, Portfolio):
            raise TypeError("portfolio must be a Portfolio.")

        if not isinstance(
            execution_simulator,
            AdvancedExecutionSimulator,
        ):
            raise TypeError(
                "execution_simulator must be an AdvancedExecutionSimulator."
            )

        self.market_data = market_data.copy()

        self.strategy = strategy
        self.position_sizer = position_sizer
        self.portfolio = portfolio
        self.execution_simulator = execution_simulator

        self.periods_per_year = periods_per_year

        self.orders: list[Order] = []
        self.fills: list[Fill] = []
        self.execution_results: list[ExecutionResult] = []
        self.signals: list[StrategySignal] = []

        self._pending: dict[
            int,
            list[PendingSignal],
        ] = defaultdict(list)

        self._validate_market_data()

    def _validate_market_data(self) -> None:
        """Validate historical data consumed by the quant engine."""
        if self.market_data.empty:
            raise ValueError("market_data cannot be empty.")

        if not isinstance(
            self.market_data.index,
            pd.DatetimeIndex,
        ):
            raise TypeError("market_data must use a DatetimeIndex.")

        if self.market_data.index.tz is None:
            raise ValueError("market_data index must be timezone-aware.")

        if self.market_data.index.has_duplicates:
            raise ValueError("market_data cannot contain duplicate timestamps.")

        if not self.market_data.index.is_monotonic_increasing:
            raise ValueError("market_data must be sorted chronologically.")

        if "close" not in self.market_data.columns:
            raise ValueError("market_data must contain a close column.")

        close = self.market_data["close"]

        if close.isna().any():
            raise ValueError("close prices cannot contain missing values.")

        if (close <= 0).any():
            raise ValueError("close prices must be strictly positive.")

        if "volume" in self.market_data.columns:
            volume = self.market_data["volume"]

            if volume.isna().any():
                raise ValueError("volume cannot contain missing values.")

            if (volume <= 0).any():
                raise ValueError("volume must be strictly positive.")

        if isinstance(
            self.periods_per_year,
            bool,
        ) or not isinstance(
            self.periods_per_year,
            int,
        ):
            raise TypeError("periods_per_year must be an integer.")

        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be greater than zero.")

    def _target_quantity(
        self,
        signal: StrategySignal,
        price: float,
    ) -> float:
        """Convert a signal into a risk-capped target position."""
        if (
            signal.direction is SignalDirection.SHORT
            and not self.strategy.config.allow_short
        ):
            return 0.0

        target_quantity = self.position_sizer.size(
            signal=signal,
            equity=self.portfolio.equity,
            price=price,
        )

        maximum_notional = (
            self.portfolio.equity * self.strategy.config.max_position_weight
        )

        maximum_quantity = maximum_notional / price

        target_quantity = max(
            -maximum_quantity,
            min(
                target_quantity,
                maximum_quantity,
            ),
        )

        return float(target_quantity)

    def _create_delta_order(
        self,
        signal: StrategySignal,
        price: float,
    ) -> Order | None:
        """Create an order for the difference between target and current."""
        position = self.portfolio.get_position(signal.symbol)

        target_quantity = self._target_quantity(
            signal,
            price,
        )

        delta_quantity = target_quantity - position.quantity

        if abs(delta_quantity) <= 1e-12:
            return None

        if delta_quantity > 0:
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL

        return Order(
            symbol=signal.symbol,
            side=side,
            quantity=abs(delta_quantity),
            timestamp=signal.timestamp,
        )

    def _execute_pending(
        self,
        *,
        bar_number: int,
        timestamp: pd.Timestamp,
        price: float,
        volume: float | None,
    ) -> None:
        """Execute all signals whose lag expires on this bar."""
        pending_signals = self._pending.pop(
            bar_number,
            [],
        )

        for pending_signal in pending_signals:
            order = self._create_delta_order(
                pending_signal.signal,
                price,
            )

            if order is None:
                continue

            order.status = OrderStatus.SUBMITTED

            self.orders.append(order)

            try:
                self.portfolio.validate_order(
                    order,
                    price,
                )
            except ValueError:
                order.status = OrderStatus.REJECTED
                continue

            execution_result = self.execution_simulator.execute(
                order=order,
                market_price=price,
                timestamp=timestamp.to_pydatetime(),
                volume=volume,
            )

            self.execution_results.append(execution_result)

            if execution_result.fill is None:
                continue

            self.portfolio.process_fill(execution_result.fill)

            self.fills.append(execution_result.fill)

    def _schedule_signal(
        self,
        *,
        signal: StrategySignal,
        bar_number: int,
    ) -> None:
        """Schedule a generated signal according to its configured lag."""
        execution_bar = bar_number + self.strategy.config.signal_lag

        self._pending[execution_bar].append(
            PendingSignal(
                signal=signal,
                execution_bar=execution_bar,
            )
        )

    def run(self) -> BacktestResult:
        """Run the complete historical simulation."""
        symbol = self.strategy.symbol

        for bar_number, (
            timestamp,
            row,
        ) in enumerate(self.market_data.iterrows()):
            price = float(row["close"])

            volume: float | None = None

            if "volume" in self.market_data.columns:
                volume = float(row["volume"])

            # Existing holdings are first marked using the
            # newly available market observation.
            self.portfolio.mark_to_market(
                {
                    symbol: price,
                }
            )

            # Signals from previous bars may execute now.
            self._execute_pending(
                bar_number=bar_number,
                timestamp=timestamp,
                price=price,
                volume=volume,
            )

            # Only after pending execution do we calculate
            # today's strategy signal.
            signal = self.strategy.update(
                price=price,
                timestamp=timestamp.to_pydatetime(),
            )

            self.signals.append(signal)

            # Today's signal cannot execute today.
            self._schedule_signal(
                signal=signal,
                bar_number=bar_number,
            )

            # Refresh marks after any fills.
            self.portfolio.mark_to_market(
                {
                    symbol: price,
                }
            )

            self.portfolio.record_equity(timestamp.to_pydatetime())

        equity_curve = pd.Series(
            {timestamp: equity for timestamp, equity in self.portfolio.equity_history},
            dtype=float,
            name="equity",
        )

        return BacktestResult(
            equity_curve=equity_curve,
            fills=tuple(self.fills),
            periods_per_year=self.periods_per_year,
        )
