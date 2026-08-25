from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from trading_engine.backtest import (
    BacktestEngine,
    ExecutionModel,
    MarketEvent,
    OrderSide,
    Portfolio,
    SignalEvent,
    Strategy,
)
from trading_engine.backtest.models import OrderStatus


class BuyOnceStrategy(Strategy):
    def __init__(self):
        self.bought = False

    def on_market(
        self,
        event,
        portfolio,
    ):
        if self.bought:
            return []

        self.bought = True

        return [
            SignalEvent(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=10,
                timestamp=event.timestamp,
            )
        ]


def make_market_data():
    index = pd.date_range(
        "2026-01-01",
        periods=4,
    )

    return {
        "AAPL": pd.DataFrame(
            {
                "close": [
                    100.0,
                    105.0,
                    110.0,
                    115.0,
                ]
            },
            index=index,
        )
    }


def test_backtest_executes_signal():
    engine = BacktestEngine(
        market_data=make_market_data(),
        strategy=BuyOnceStrategy(),
        portfolio=Portfolio(100_000),
        execution_model=ExecutionModel(),
    )

    result = engine.run()

    assert len(result.fills) == 1


def test_backtest_produces_equity_curve():
    engine = BacktestEngine(
        market_data=make_market_data(),
        strategy=BuyOnceStrategy(),
        portfolio=Portfolio(100_000),
        execution_model=ExecutionModel(),
    )

    result = engine.run()

    assert len(result.equity_curve) == 4


def test_profitable_position_increases_equity():
    engine = BacktestEngine(
        market_data=make_market_data(),
        strategy=BuyOnceStrategy(),
        portfolio=Portfolio(100_000),
        execution_model=ExecutionModel(),
    )

    result = engine.run()

    assert result.equity_curve.iloc[-1] > result.equity_curve.iloc[0]


class NoOpStrategy(Strategy):
    def on_market(
        self,
        event,
        portfolio,
    ):
        return []


class TooExpensiveStrategy(Strategy):
    def on_market(
        self,
        event,
        portfolio,
    ):
        return [
            SignalEvent(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=1_000_000,
                timestamp=event.timestamp,
            )
        ]


def test_engine_rejects_empty_market_data():
    with pytest.raises(ValueError, match="cannot be empty"):
        BacktestEngine(
            market_data={},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_rejects_empty_symbol_frame():
    frame = pd.DataFrame(
        columns=["close"],
        index=pd.DatetimeIndex([]),
    )

    with pytest.raises(ValueError, match="empty"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_requires_close_column():
    index = pd.date_range(
        "2026-01-01",
        periods=2,
    )

    frame = pd.DataFrame(
        {"open": [100, 101]},
        index=index,
    )

    with pytest.raises(ValueError, match="close"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_requires_datetime_index():
    frame = pd.DataFrame({"close": [100.0, 101.0]})

    with pytest.raises(TypeError, match="DatetimeIndex"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_rejects_duplicate_timestamps():
    timestamp = pd.Timestamp("2026-01-01")

    frame = pd.DataFrame(
        {"close": [100.0, 101.0]},
        index=pd.DatetimeIndex([timestamp, timestamp]),
    )

    with pytest.raises(ValueError, match="duplicate"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_rejects_unsorted_market_data():
    index = pd.DatetimeIndex(
        [
            "2026-01-02",
            "2026-01-01",
        ]
    )

    frame = pd.DataFrame(
        {"close": [101.0, 100.0]},
        index=index,
    )

    with pytest.raises(ValueError, match="sorted"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_rejects_missing_close_prices():
    index = pd.date_range(
        "2026-01-01",
        periods=2,
    )

    frame = pd.DataFrame(
        {"close": [100.0, np.nan]},
        index=index,
    )

    with pytest.raises(ValueError, match="missing"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_rejects_non_positive_close_prices():
    index = pd.date_range(
        "2026-01-01",
        periods=2,
    )

    frame = pd.DataFrame(
        {"close": [100.0, 0.0]},
        index=index,
    )

    with pytest.raises(ValueError, match="non-positive"):
        BacktestEngine(
            market_data={"AAPL": frame},
            strategy=NoOpStrategy(),
            portfolio=Portfolio(100_000),
            execution_model=ExecutionModel(),
        )


def test_engine_rejects_market_data_without_common_timestamps():
    first = pd.DataFrame(
        {"close": [100.0]},
        index=pd.DatetimeIndex(["2026-01-01"]),
    )

    second = pd.DataFrame(
        {"close": [200.0]},
        index=pd.DatetimeIndex(["2026-01-02"]),
    )

    engine = BacktestEngine(
        market_data={
            "AAPL": first,
            "MSFT": second,
        },
        strategy=NoOpStrategy(),
        portfolio=Portfolio(100_000),
        execution_model=ExecutionModel(),
    )

    with pytest.raises(ValueError, match="no common"):
        engine.run()


def test_rejected_order_is_recorded_as_rejected():
    engine = BacktestEngine(
        market_data=make_market_data(),
        strategy=TooExpensiveStrategy(),
        portfolio=Portfolio(100),
        execution_model=ExecutionModel(),
    )

    engine.run()

    assert engine.orders
    assert engine.orders[0].status is OrderStatus.REJECTED


def test_no_op_strategy_produces_no_fills():
    engine = BacktestEngine(
        market_data=make_market_data(),
        strategy=NoOpStrategy(),
        portfolio=Portfolio(100_000),
        execution_model=ExecutionModel(),
    )

    result = engine.run()

    assert result.fills == ()


def test_strategy_base_method_raises_not_implemented():
    class ConcreteStrategy(Strategy):
        def on_market(
            self,
            event,
            portfolio,
        ):
            return super().on_market(
                event,
                portfolio,
            )

    strategy = ConcreteStrategy()

    event = MarketEvent(
        timestamp=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
        prices={"AAPL": 100.0},
    )

    with pytest.raises(NotImplementedError):
        strategy.on_market(
            event,
            Portfolio(100_000),
        )
