from datetime import UTC, datetime

import pytest

from trading_engine.backtest.models import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
)
from trading_engine.execution import (
    AdvancedExecutionSimulator,
    BidAskSpreadModel,
    ConstantBpsSlippage,
    FixedCommission,
    ParticipationRateModel,
    PercentageCommission,
    SquareRootMarketImpact,
)


def timestamp():
    return datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )


def test_market_order_fills_completely_without_constraints():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is not None
    assert result.filled_quantity == pytest.approx(100)
    assert result.remaining_quantity == pytest.approx(0)
    assert result.status is OrderStatus.FILLED


def test_liquidity_causes_partial_fill():
    simulator = AdvancedExecutionSimulator(
        liquidity_model=ParticipationRateModel(
            max_participation_rate=0.10,
        )
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        20_000,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
        volume=100_000,
    )

    assert result.fill is not None

    assert result.filled_quantity == pytest.approx(10_000)

    assert result.remaining_quantity == pytest.approx(10_000)

    assert result.status is (OrderStatus.PARTIALLY_FILLED)

    assert result.fill_fraction == pytest.approx(0.5)


def test_commission_is_applied():
    simulator = AdvancedExecutionSimulator(
        commission_model=FixedCommission(
            amount=5,
        )
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is not None
    assert result.fill.commission == pytest.approx(5)


def test_percentage_commission_is_applied():
    simulator = AdvancedExecutionSimulator(
        commission_model=PercentageCommission(
            rate=0.001,
        )
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is not None
    assert result.fill.commission == pytest.approx(10)


def test_spread_and_slippage_worsen_buy_price():
    simulator = AdvancedExecutionSimulator(
        spread_model=BidAskSpreadModel(
            half_spread_bps=5,
        ),
        slippage_model=ConstantBpsSlippage(
            bps=10,
        ),
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is not None
    assert result.fill.price > 100


def test_spread_and_slippage_worsen_sell_price():
    simulator = AdvancedExecutionSimulator(
        spread_model=BidAskSpreadModel(
            half_spread_bps=5,
        ),
        slippage_model=ConstantBpsSlippage(
            bps=10,
        ),
    )

    order = Order(
        "AAPL",
        OrderSide.SELL,
        100,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is not None
    assert result.fill.price < 100


def test_market_impact_worsens_execution():
    simulator = AdvancedExecutionSimulator(
        liquidity_model=ParticipationRateModel(
            max_participation_rate=1.0,
        ),
        impact_model=SquareRootMarketImpact(
            coefficient_bps=100,
        ),
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        10_000,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
        volume=100_000,
    )

    assert result.fill is not None
    assert result.fill.price > 100


def test_buy_limit_not_reached_produces_no_fill():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
        order_type=OrderType.LIMIT,
        limit_price=95,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is None
    assert result.filled_quantity == 0


def test_sell_limit_not_reached_produces_no_fill():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.SELL,
        100,
        order_type=OrderType.LIMIT,
        limit_price=105,
    )

    result = simulator.execute(
        order=order,
        market_price=100,
        timestamp=timestamp(),
    )

    assert result.fill is None


def test_execution_requires_volume_for_liquidity_model():
    simulator = AdvancedExecutionSimulator(liquidity_model=ParticipationRateModel())

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    with pytest.raises(
        ValueError,
        match="volume is required",
    ):
        simulator.execute(
            order=order,
            market_price=100,
            timestamp=timestamp(),
        )


def test_execution_requires_volume_for_market_impact():
    simulator = AdvancedExecutionSimulator(impact_model=SquareRootMarketImpact())

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    with pytest.raises(
        ValueError,
        match="volume is required",
    ):
        simulator.execute(
            order=order,
            market_price=100,
            timestamp=timestamp(),
        )


def test_invalid_market_price_is_rejected():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        simulator.execute(
            order=order,
            market_price=0,
            timestamp=timestamp(),
        )


def test_naive_timestamp_is_rejected():
    simulator = AdvancedExecutionSimulator()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        100,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        simulator.execute(
            order=order,
            market_price=100,
            timestamp=datetime(2026, 1, 1),  # noqa: DTZ001
        )
