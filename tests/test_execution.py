from datetime import UTC, datetime

import numpy as np
import pytest

from trading_engine.backtest.execution import (
    ExecutionModel,
)
from trading_engine.backtest.models import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
)


def test_market_order_executes():
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        10,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill is not None
    assert fill.price == pytest.approx(100)


def test_buy_slippage_is_adverse():
    execution = ExecutionModel(
        slippage_bps=10,
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill.price > 100


def test_sell_slippage_is_adverse():
    execution = ExecutionModel(
        slippage_bps=10,
    )

    order = Order(
        "AAPL",
        OrderSide.SELL,
        1,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill.price < 100


def test_commission_calculation():
    execution = ExecutionModel(
        commission_rate=0.001,
        fixed_commission=1,
    )

    order = Order(
        "AAPL",
        OrderSide.BUY,
        10,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill.commission == pytest.approx(2)


def test_buy_limit_not_reached():
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
        order_type=OrderType.LIMIT,
        limit_price=95,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commission_rate", -0.01),
        ("fixed_commission", -1.0),
        ("slippage_bps", -1.0),
    ],
)
def test_execution_model_rejects_negative_configuration(field, value):
    kwargs = {field: value}

    with pytest.raises(ValueError, match="negative"):
        ExecutionModel(**kwargs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commission_rate", "0.01"),
        ("fixed_commission", True),
        ("slippage_bps", "10"),
    ],
)
def test_execution_model_rejects_non_numeric_configuration(field, value):
    kwargs = {field: value}

    with pytest.raises(TypeError, match="numeric"):
        ExecutionModel(**kwargs)


def test_execution_model_rejects_non_finite_configuration():
    with pytest.raises(ValueError, match="finite"):
        ExecutionModel(
            commission_rate=np.inf,
        )


@pytest.mark.parametrize("price", [0, -100])
def test_execution_rejects_non_positive_market_price(price):
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
    )

    with pytest.raises(ValueError, match="greater than zero"):
        execution.execute(
            order,
            price,
            datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_sell_limit_not_reached():
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.SELL,
        1,
        order_type=OrderType.LIMIT,
        limit_price=105,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill is None


def test_buy_limit_executes_when_reached():
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
        order_type=OrderType.LIMIT,
        limit_price=105,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill is not None


def test_sell_limit_executes_when_reached():
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.SELL,
        1,
        order_type=OrderType.LIMIT,
        limit_price=95,
    )

    fill = execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert fill is not None


def test_execution_marks_order_filled():
    execution = ExecutionModel()

    order = Order(
        "AAPL",
        OrderSide.BUY,
        1,
    )

    execution.execute(
        order,
        100,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert order.status is OrderStatus.FILLED
