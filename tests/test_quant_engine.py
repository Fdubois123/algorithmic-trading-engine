from datetime import UTC

import numpy as np
import pandas as pd
import pytest

from trading_engine.backtest import Portfolio
from trading_engine.backtest.models import (
    OrderSide,
    OrderStatus,
)
from trading_engine.backtest.quant_engine import (
    QuantBacktestEngine,
)
from trading_engine.execution import (
    AdvancedExecutionSimulator,
    BidAskSpreadModel,
    FixedCommission,
    ParticipationRateModel,
)
from trading_engine.strategies import (
    FixedFractionSizer,
    SignalDirection,
    StrategyConfig,
    StrategySignal,
)
from trading_engine.strategies.base import (
    QuantStrategy,
)


class AlwaysLongStrategy(QuantStrategy):
    """Strategy that always requests full long exposure."""

    def update(
        self,
        *,
        price,
        timestamp,
    ):
        return StrategySignal(
            symbol=self.symbol,
            direction=SignalDirection.LONG,
            timestamp=timestamp,
            strength=1.0,
        )


class AlwaysShortStrategy(QuantStrategy):
    """Strategy that always requests short exposure."""

    def update(
        self,
        *,
        price,
        timestamp,
    ):
        return StrategySignal(
            symbol=self.symbol,
            direction=SignalDirection.SHORT,
            timestamp=timestamp,
            strength=1.0,
        )


class AlwaysFlatStrategy(QuantStrategy):
    """Strategy that always requests a flat position."""

    def update(
        self,
        *,
        price,
        timestamp,
    ):
        return StrategySignal(
            symbol=self.symbol,
            direction=SignalDirection.FLAT,
            timestamp=timestamp,
            strength=0.0,
        )


def make_market_data() -> pd.DataFrame:
    index = pd.date_range(
        "2026-01-01",
        periods=4,
        tz=UTC,
    )

    return pd.DataFrame(
        {
            "close": [
                100.0,
                110.0,
                120.0,
                130.0,
            ],
            "volume": [
                100_000.0,
                100_000.0,
                100_000.0,
                100_000.0,
            ],
        },
        index=index,
    )


def make_engine(
    *,
    strategy=None,
    position_sizer=None,
    portfolio=None,
    execution_simulator=None,
    data=None,
) -> QuantBacktestEngine:
    if strategy is None:
        strategy = AlwaysLongStrategy(
            symbol="AAPL",
        )

    if position_sizer is None:
        position_sizer = FixedFractionSizer(
            fraction=0.10,
        )

    if portfolio is None:
        portfolio = Portfolio(
            100_000,
        )

    if execution_simulator is None:
        execution_simulator = AdvancedExecutionSimulator()

    if data is None:
        data = make_market_data()

    return QuantBacktestEngine(
        market_data=data,
        strategy=strategy,
        position_sizer=position_sizer,
        portfolio=portfolio,
        execution_simulator=execution_simulator,
    )


def test_signal_does_not_execute_on_same_bar():
    engine = make_engine()

    result = engine.run()

    assert result.fills

    first_fill = result.fills[0]

    # Signal observed price 100 on bar 0.
    # Earliest execution must therefore use bar 1 price.
    assert first_fill.price == pytest.approx(110.0)


def test_default_signal_lag_is_one_bar():
    strategy = AlwaysLongStrategy(
        symbol="AAPL",
    )

    assert strategy.config.signal_lag == 1


def test_two_bar_signal_lag_executes_two_bars_later():
    engine = make_engine(
        strategy=AlwaysLongStrategy(
            symbol="AAPL",
            config=StrategyConfig(
                signal_lag=2,
            ),
        )
    )

    result = engine.run()

    assert result.fills

    assert result.fills[0].price == pytest.approx(120.0)


def test_zero_signal_lag_is_rejected():
    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        StrategyConfig(
            signal_lag=0,
        )


def test_flat_strategy_generates_no_orders():
    engine = make_engine(
        strategy=AlwaysFlatStrategy(
            symbol="AAPL",
        )
    )

    result = engine.run()

    assert result.fills == ()
    assert engine.orders == []


def test_long_strategy_creates_buy_fill():
    engine = make_engine()

    result = engine.run()

    assert result.fills

    assert result.fills[0].side is OrderSide.BUY


def test_target_position_does_not_accumulate_full_order_each_bar():
    engine = make_engine()

    engine.run()

    position = engine.portfolio.positions["AAPL"]

    assert position.quantity > 0

    # A target-position system should rebalance toward
    # the requested exposure, rather than repeatedly
    # buying the full target quantity from zero.
    assert position.quantity < 200


def test_max_position_weight_caps_quantity():
    engine = make_engine(
        strategy=AlwaysLongStrategy(
            symbol="AAPL",
            config=StrategyConfig(
                max_position_weight=0.05,
            ),
        ),
        position_sizer=FixedFractionSizer(
            fraction=1.0,
        ),
    )

    engine.run()

    position = engine.portfolio.positions["AAPL"]

    initial_cap = 100_000 * 0.05 / 110

    assert position.quantity <= (initial_cap + 1e-9)


def test_execution_costs_reduce_final_equity():
    frictionless = make_engine().run()

    costly = make_engine(
        execution_simulator=AdvancedExecutionSimulator(
            commission_model=FixedCommission(
                amount=10.0,
            ),
            spread_model=BidAskSpreadModel(
                half_spread_bps=20,
            ),
        )
    ).run()

    assert costly.equity_curve.iloc[-1] < frictionless.equity_curve.iloc[-1]


def test_liquidity_constraint_produces_partial_fill():
    engine = make_engine(
        position_sizer=FixedFractionSizer(
            fraction=1.0,
        ),
        portfolio=Portfolio(
            1_000_000,
        ),
        execution_simulator=AdvancedExecutionSimulator(
            liquidity_model=ParticipationRateModel(
                max_participation_rate=0.001,
            )
        ),
    )

    engine.run()

    assert any(
        execution.status is OrderStatus.PARTIALLY_FILLED
        for execution in engine.execution_results
    )


def test_execution_results_are_recorded():
    engine = make_engine()

    engine.run()

    assert engine.execution_results


def test_signals_are_recorded_for_each_bar():
    engine = make_engine()

    engine.run()

    assert len(engine.signals) == len(make_market_data())


def test_equity_curve_has_one_value_per_bar():
    engine = make_engine()

    result = engine.run()

    assert len(result.equity_curve) == 4


def test_empty_market_data_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        make_engine(
            data=pd.DataFrame(),
        )


def test_market_data_must_be_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        QuantBacktestEngine(
            market_data="invalid",
            strategy=AlwaysLongStrategy(
                symbol="AAPL",
            ),
            position_sizer=FixedFractionSizer(),
            portfolio=Portfolio(100_000),
            execution_simulator=AdvancedExecutionSimulator(),
        )


def test_market_data_requires_datetime_index():
    frame = pd.DataFrame(
        {
            "close": [
                100.0,
                101.0,
            ]
        }
    )

    with pytest.raises(
        TypeError,
        match="DatetimeIndex",
    ):
        make_engine(
            data=frame,
        )


def test_naive_datetime_index_is_rejected():
    frame = pd.DataFrame(
        {
            "close": [
                100.0,
                101.0,
            ],
        },
        index=pd.date_range(
            "2026-01-01",
            periods=2,
        ),
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        make_engine(
            data=frame,
        )


def test_duplicate_timestamps_are_rejected():
    duplicate = pd.Timestamp(
        "2026-01-01",
        tz=UTC,
    )

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
                101.0,
            ],
        },
        index=pd.DatetimeIndex(
            [
                duplicate,
                duplicate,
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        make_engine(
            data=frame,
        )


def test_unsorted_market_data_is_rejected():
    frame = pd.DataFrame(
        {
            "close": [
                101.0,
                100.0,
            ],
        },
        index=pd.DatetimeIndex(
            [
                pd.Timestamp(
                    "2026-01-02",
                    tz=UTC,
                ),
                pd.Timestamp(
                    "2026-01-01",
                    tz=UTC,
                ),
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match="sorted",
    ):
        make_engine(
            data=frame,
        )


def test_close_column_is_required():
    frame = pd.DataFrame(
        {
            "open": [
                100.0,
                101.0,
            ]
        },
        index=pd.date_range(
            "2026-01-01",
            periods=2,
            tz=UTC,
        ),
    )

    with pytest.raises(
        ValueError,
        match="close",
    ):
        make_engine(
            data=frame,
        )


def test_missing_close_price_is_rejected():
    frame = pd.DataFrame(
        {
            "close": [
                100.0,
                np.nan,
            ]
        },
        index=pd.date_range(
            "2026-01-01",
            periods=2,
            tz=UTC,
        ),
    )

    with pytest.raises(
        ValueError,
        match="missing",
    ):
        make_engine(
            data=frame,
        )


@pytest.mark.parametrize(
    "price",
    [
        0.0,
        -1.0,
    ],
)
def test_non_positive_close_price_is_rejected(
    price,
):
    frame = pd.DataFrame(
        {
            "close": [
                100.0,
                price,
            ]
        },
        index=pd.date_range(
            "2026-01-01",
            periods=2,
            tz=UTC,
        ),
    )

    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        make_engine(
            data=frame,
        )


def test_missing_volume_is_rejected():
    frame = make_market_data()

    frame.loc[
        frame.index[1],
        "volume",
    ] = np.nan

    with pytest.raises(
        ValueError,
        match="volume",
    ):
        make_engine(
            data=frame,
        )


def test_non_positive_volume_is_rejected():
    frame = make_market_data()

    frame.loc[
        frame.index[1],
        "volume",
    ] = 0.0

    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        make_engine(
            data=frame,
        )


@pytest.mark.parametrize(
    "periods",
    [
        252.5,
        "252",
        True,
    ],
)
def test_periods_per_year_must_be_integer(
    periods,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        QuantBacktestEngine(
            market_data=make_market_data(),
            strategy=AlwaysLongStrategy(
                symbol="AAPL",
            ),
            position_sizer=FixedFractionSizer(),
            portfolio=Portfolio(100_000),
            execution_simulator=AdvancedExecutionSimulator(),
            periods_per_year=periods,
        )


@pytest.mark.parametrize(
    "periods",
    [
        0,
        -1,
    ],
)
def test_periods_per_year_must_be_positive(
    periods,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        QuantBacktestEngine(
            market_data=make_market_data(),
            strategy=AlwaysLongStrategy(
                symbol="AAPL",
            ),
            position_sizer=FixedFractionSizer(),
            portfolio=Portfolio(100_000),
            execution_simulator=AdvancedExecutionSimulator(),
            periods_per_year=periods,
        )


def test_short_signal_is_ignored_when_shorting_disabled():
    engine = make_engine(
        strategy=AlwaysShortStrategy(
            symbol="AAPL",
            config=StrategyConfig(
                allow_short=False,
            ),
        )
    )

    result = engine.run()

    assert result.fills == ()


def test_short_strategy_can_execute_when_enabled():
    engine = make_engine(
        strategy=AlwaysShortStrategy(
            symbol="AAPL",
            config=StrategyConfig(
                allow_short=True,
            ),
        ),
        portfolio=Portfolio(
            100_000,
            allow_short=True,
        ),
    )

    result = engine.run()

    assert result.fills
    assert result.fills[0].side is OrderSide.SELL


def test_pending_signal_beyond_final_bar_does_not_execute():
    engine = make_engine(
        strategy=AlwaysLongStrategy(
            symbol="AAPL",
            config=StrategyConfig(
                signal_lag=10,
            ),
        )
    )

    result = engine.run()

    assert result.fills == ()
