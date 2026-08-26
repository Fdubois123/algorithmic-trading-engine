from datetime import UTC, datetime

import numpy as np
import pytest

from trading_engine.backtest.models import (
    Order,
    OrderSide,
    OrderType,
)
from trading_engine.execution import (
    AdvancedExecutionSimulator,
    BidAskSpreadModel,
    ConstantBpsSlippage,
    ParticipationRateModel,
    SquareRootMarketImpact,
)
from trading_engine.strategies import (
    FixedFractionSizer,
    QuantStrategy,
    SignalDirection,
    StrategyConfig,
    StrategySignal,
    VolatilityBreakoutStrategy,
    VolatilityTargetSizer,
    ZScoreMeanReversionStrategy,
)
from trading_engine.strategies.base import (
    validate_market_price,
    validate_positive_integer,
    validate_strategy_symbol,
    validate_timestamp,
)


def timestamp(day: int = 1) -> datetime:
    return datetime(
        2026,
        1,
        day,
        tzinfo=UTC,
    )


# ---------------------------------------------------------------------------
# Strategy base validation
# ---------------------------------------------------------------------------


def test_strategy_symbol_rejects_non_string():
    with pytest.raises(TypeError, match="string"):
        validate_strategy_symbol(123)


def test_strategy_symbol_rejects_empty_string():
    with pytest.raises(ValueError, match="empty"):
        validate_strategy_symbol("   ")


@pytest.mark.parametrize("price", ["100", True])
def test_market_price_rejects_non_numeric_values(price):
    with pytest.raises(TypeError, match="numeric"):
        validate_market_price(price)


def test_market_price_rejects_non_finite_value():
    with pytest.raises(ValueError, match="finite"):
        validate_market_price(np.inf)


@pytest.mark.parametrize("price", [0, -1])
def test_market_price_rejects_non_positive_values(price):
    with pytest.raises(ValueError, match="greater than zero"):
        validate_market_price(price)


def test_timestamp_rejects_non_datetime():
    with pytest.raises(TypeError, match="datetime"):
        validate_timestamp("2026-01-01")


def test_timestamp_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        validate_timestamp(
            datetime(2026, 1, 1),  # noqa: DTZ001
        )


@pytest.mark.parametrize("value", [1.5, "2", True])
def test_positive_integer_rejects_non_integer_values(value):
    with pytest.raises(TypeError, match="integer"):
        validate_positive_integer(
            value,
            name="window",
        )


@pytest.mark.parametrize("value", [0, -1])
def test_positive_integer_rejects_non_positive_values(value):
    with pytest.raises(ValueError, match="greater than zero"):
        validate_positive_integer(
            value,
            name="window",
        )


def test_quant_strategy_rejects_invalid_config():
    class DummyStrategy(QuantStrategy):
        def update(
            self,
            *,
            price,
            timestamp,
        ):
            return StrategySignal(
                self.symbol,
                SignalDirection.FLAT,
                timestamp,
                strength=0.0,
            )

    with pytest.raises(TypeError, match="StrategyConfig"):
        DummyStrategy(
            symbol="AAPL",
            config="invalid",
        )


def test_quant_strategy_abstract_update_contract():
    class DummyStrategy(QuantStrategy):
        def update(
            self,
            *,
            price,
            timestamp,
        ):
            return super().update(
                price=price,
                timestamp=timestamp,
            )

    strategy = DummyStrategy(
        symbol="AAPL",
    )

    with pytest.raises(NotImplementedError):
        strategy.update(
            price=100,
            timestamp=timestamp(),
        )


# ---------------------------------------------------------------------------
# Position sizing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fraction", ["0.1", True])
def test_fixed_fraction_rejects_non_numeric_fraction(fraction):
    with pytest.raises(TypeError, match="numeric"):
        FixedFractionSizer(
            fraction=fraction,
        )


def test_fixed_fraction_rejects_non_finite_fraction():
    with pytest.raises(ValueError, match="finite"):
        FixedFractionSizer(
            fraction=np.inf,
        )


def test_fixed_fraction_rejects_non_numeric_equity():
    sizer = FixedFractionSizer()

    signal = StrategySignal(
        "AAPL",
        SignalDirection.LONG,
        timestamp(),
    )

    with pytest.raises(TypeError, match="numeric"):
        sizer.size(
            signal=signal,
            equity="100000",
            price=100,
        )


def test_fixed_fraction_rejects_non_numeric_price():
    sizer = FixedFractionSizer()

    signal = StrategySignal(
        "AAPL",
        SignalDirection.LONG,
        timestamp(),
    )

    with pytest.raises(TypeError, match="numeric"):
        sizer.size(
            signal=signal,
            equity=100_000,
            price=True,
        )


def test_volatility_sizer_flat_signal_returns_zero():
    sizer = VolatilityTargetSizer()

    signal = StrategySignal(
        "AAPL",
        SignalDirection.FLAT,
        timestamp(),
    )

    result = sizer.size(
        signal=signal,
        equity=100_000,
        price=100,
    )

    assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Mean reversion
# ---------------------------------------------------------------------------


def test_mean_reversion_window_must_be_at_least_two():
    with pytest.raises(ValueError, match="at least 2"):
        ZScoreMeanReversionStrategy(
            symbol="AAPL",
            window=1,
        )


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("entry_z", "2"),
        ("exit_z", True),
    ],
)
def test_mean_reversion_rejects_non_numeric_thresholds(
    parameter,
    value,
):
    kwargs = {
        parameter: value,
    }

    with pytest.raises(TypeError, match="numeric"):
        ZScoreMeanReversionStrategy(
            symbol="AAPL",
            **kwargs,
        )


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("entry_z", np.inf),
        ("exit_z", np.nan),
    ],
)
def test_mean_reversion_rejects_non_finite_thresholds(
    parameter,
    value,
):
    kwargs = {
        parameter: value,
    }

    with pytest.raises(ValueError, match="finite"):
        ZScoreMeanReversionStrategy(
            symbol="AAPL",
            **kwargs,
        )


def test_mean_reversion_rejects_non_positive_entry_z():
    with pytest.raises(ValueError, match="greater than zero"):
        ZScoreMeanReversionStrategy(
            symbol="AAPL",
            entry_z=0,
        )


def test_mean_reversion_rejects_negative_exit_z():
    with pytest.raises(ValueError, match="negative"):
        ZScoreMeanReversionStrategy(
            symbol="AAPL",
            exit_z=-0.1,
        )


def test_mean_reversion_state_property():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
    )

    assert strategy.state is SignalDirection.FLAT


def test_short_mean_reversion_position_exits():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
        config=StrategyConfig(
            allow_short=True,
        ),
    )

    strategy.update(
        price=100,
        timestamp=timestamp(1),
    )
    strategy.update(
        price=100,
        timestamp=timestamp(2),
    )

    signal = strategy.update(
        price=110,
        timestamp=timestamp(3),
    )

    assert signal.direction is SignalDirection.SHORT

    signal = strategy.update(
        price=100,
        timestamp=timestamp(4),
    )

    assert signal.direction is SignalDirection.FLAT


# ---------------------------------------------------------------------------
# Volatility breakout
# ---------------------------------------------------------------------------


def test_volatility_breakout_requires_lookback_of_at_least_two():
    with pytest.raises(ValueError, match="at least 2"):
        VolatilityBreakoutStrategy(
            symbol="AAPL",
            lookback=1,
        )


def test_volatility_breakout_rejects_non_numeric_multiplier():
    with pytest.raises(TypeError, match="numeric"):
        VolatilityBreakoutStrategy(
            symbol="AAPL",
            breakout_multiplier="2",
        )


def test_volatility_breakout_rejects_non_finite_multiplier():
    with pytest.raises(ValueError, match="finite"):
        VolatilityBreakoutStrategy(
            symbol="AAPL",
            breakout_multiplier=np.inf,
        )


def test_zero_historical_volatility_breakout_has_full_strength():
    strategy = VolatilityBreakoutStrategy(
        symbol="AAPL",
        lookback=2,
        breakout_multiplier=2.0,
    )

    strategy.update(
        price=100,
        timestamp=timestamp(1),
    )
    strategy.update(
        price=100,
        timestamp=timestamp(2),
    )
    strategy.update(
        price=100,
        timestamp=timestamp(3),
    )

    signal = strategy.update(
        price=110,
        timestamp=timestamp(4),
    )

    assert signal.direction is SignalDirection.LONG
    assert signal.strength == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Execution validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bps", ["10", True])
def test_slippage_rejects_non_numeric_bps(bps):
    with pytest.raises(TypeError, match="numeric"):
        ConstantBpsSlippage(
            bps=bps,
        )


def test_slippage_rejects_non_finite_bps():
    with pytest.raises(ValueError, match="finite"):
        ConstantBpsSlippage(
            bps=np.inf,
        )


def test_spread_rejects_non_numeric_bps():
    with pytest.raises(TypeError, match="numeric"):
        BidAskSpreadModel(
            half_spread_bps="5",
        )


def test_spread_rejects_non_finite_bps():
    with pytest.raises(ValueError, match="finite"):
        BidAskSpreadModel(
            half_spread_bps=np.inf,
        )


def test_liquidity_rejects_non_numeric_participation_rate():
    with pytest.raises(TypeError, match="numeric"):
        ParticipationRateModel(
            max_participation_rate="0.1",
        )


def test_liquidity_rejects_non_finite_participation_rate():
    with pytest.raises(ValueError, match="finite"):
        ParticipationRateModel(
            max_participation_rate=np.inf,
        )


def test_liquidity_rejects_non_numeric_volume():
    model = ParticipationRateModel()

    with pytest.raises(TypeError, match="numeric"):
        model.maximum_quantity(
            volume="100000",
        )


def test_liquidity_rejects_non_finite_volume():
    model = ParticipationRateModel()

    with pytest.raises(ValueError, match="finite"):
        model.maximum_quantity(
            volume=np.inf,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("coefficient_bps", "25"),
        ("max_impact_bps", True),
    ],
)
def test_market_impact_rejects_non_numeric_configuration(
    field,
    value,
):
    with pytest.raises(TypeError, match="numeric"):
        SquareRootMarketImpact(
            **{field: value},
        )


def test_market_impact_rejects_non_finite_configuration():
    with pytest.raises(ValueError, match="finite"):
        SquareRootMarketImpact(
            coefficient_bps=np.inf,
        )


def test_market_impact_rejects_negative_configuration():
    with pytest.raises(ValueError, match="negative"):
        SquareRootMarketImpact(
            coefficient_bps=-1,
        )


def test_market_impact_rejects_zero_volume():
    model = SquareRootMarketImpact()

    with pytest.raises(ValueError, match="volume"):
        model.impact_bps(
            quantity=100,
            volume=0,
        )


# ---------------------------------------------------------------------------
# Advanced execution
# ---------------------------------------------------------------------------


def test_simulator_rejects_non_numeric_market_price():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
    )

    with pytest.raises(TypeError, match="numeric"):
        simulator.execute(
            order=order,
            market_price="100",
            timestamp=timestamp(),
        )


def test_simulator_rejects_non_finite_market_price():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
    )

    with pytest.raises(ValueError, match="finite"):
        simulator.execute(
            order=order,
            market_price=np.inf,
            timestamp=timestamp(),
        )


def test_simulator_rejects_non_datetime_timestamp():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
    )

    with pytest.raises(TypeError, match="datetime"):
        simulator.execute(
            order=order,
            market_price=100,
            timestamp="2026-01-01",
        )


def test_buy_limit_can_be_invalidated_by_execution_friction():
    simulator = AdvancedExecutionSimulator(
        spread_model=BidAskSpreadModel(
            half_spread_bps=20,
        )
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        10,
        order_type=OrderType.LIMIT,
        limit_price=100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is None
    assert result.filled_quantity == pytest.approx(0.0)
    assert result.remaining_quantity == pytest.approx(10.0)


def test_sell_limit_can_be_invalidated_by_execution_friction():
    simulator = AdvancedExecutionSimulator(
        spread_model=BidAskSpreadModel(
            half_spread_bps=20,
        )
    )

    order = Order(
        "AAPL",
        OrderSide.SELL,
        10,
        order_type=OrderType.LIMIT,
        limit_price=100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is None
    assert result.filled_quantity == pytest.approx(0.0)
    assert result.remaining_quantity == pytest.approx(10.0)
