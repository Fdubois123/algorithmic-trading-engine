import numpy as np
import pytest

from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderSide,
    OrderType,
    Position,
)


def test_market_order_creation():
    order = Order(
        symbol="aapl",
        side=OrderSide.BUY,
        quantity=10,
    )

    assert order.symbol == "AAPL"


def test_limit_order_requires_price():
    with pytest.raises(ValueError):
        Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
        )


def test_fill_notional():
    fill = Fill(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=5,
        price=100,
    )

    assert fill.notional == pytest.approx(500)


def test_long_position_pnl():
    position = Position("AAPL")

    position.apply_fill(
        Fill(
            "AAPL",
            OrderSide.BUY,
            10,
            100,
        )
    )

    position.mark(110)

    assert position.unrealized_pnl == pytest.approx(100)


def test_short_position_pnl():
    position = Position("AAPL")

    position.apply_fill(
        Fill(
            "AAPL",
            OrderSide.SELL,
            10,
            100,
        )
    )

    position.mark(90)

    assert position.unrealized_pnl == pytest.approx(100)


def test_realized_long_profit():
    position = Position("AAPL")

    position.apply_fill(
        Fill(
            "AAPL",
            OrderSide.BUY,
            10,
            100,
        )
    )

    position.apply_fill(
        Fill(
            "AAPL",
            OrderSide.SELL,
            10,
            120,
        )
    )

    assert position.realized_pnl == pytest.approx(200)

    assert position.is_flat


def test_position_reversal():
    position = Position("AAPL")

    position.apply_fill(
        Fill(
            "AAPL",
            OrderSide.BUY,
            10,
            100,
        )
    )

    position.apply_fill(
        Fill(
            "AAPL",
            OrderSide.SELL,
            15,
            110,
        )
    )

    assert position.quantity == pytest.approx(-5)
    assert position.average_price == pytest.approx(110)
    assert position.realized_pnl == pytest.approx(100)


@pytest.mark.parametrize("symbol", [123, None])
def test_order_rejects_non_string_symbol(symbol):
    with pytest.raises(TypeError, match="string"):
        Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=1,
        )


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError, match="greater than zero"):
        Order(
            "AAPL",
            OrderSide.BUY,
            quantity,
        )


@pytest.mark.parametrize("quantity", ["1", True])
def test_order_rejects_non_numeric_quantity(quantity):
    with pytest.raises(TypeError, match="numeric"):
        Order(
            "AAPL",
            OrderSide.BUY,
            quantity,
        )


def test_order_rejects_non_finite_quantity():
    with pytest.raises(ValueError, match="finite"):
        Order(
            "AAPL",
            OrderSide.BUY,
            np.inf,
        )


def test_order_rejects_invalid_side():
    with pytest.raises(TypeError, match="OrderSide"):
        Order(
            "AAPL",
            "BUY",
            1,
        )


def test_order_rejects_invalid_order_type():
    with pytest.raises(TypeError, match="OrderType"):
        Order(
            "AAPL",
            OrderSide.BUY,
            1,
            order_type="MARKET",
        )


def test_order_rejects_invalid_status():
    with pytest.raises(TypeError, match="OrderStatus"):
        Order(
            "AAPL",
            OrderSide.BUY,
            1,
            status="CREATED",
        )


def test_limit_order_rejects_invalid_limit_price():
    with pytest.raises(ValueError, match="greater than zero"):
        Order(
            "AAPL",
            OrderSide.BUY,
            1,
            order_type=OrderType.LIMIT,
            limit_price=0,
        )


def test_market_order_rejects_limit_price():
    with pytest.raises(ValueError, match="only valid"):
        Order(
            "AAPL",
            OrderSide.BUY,
            1,
            limit_price=100,
        )


def test_order_rejects_invalid_timestamp():
    with pytest.raises(TypeError, match="datetime"):
        Order(
            "AAPL",
            OrderSide.BUY,
            1,
            timestamp="2026-01-01",
        )


def test_fill_rejects_invalid_side():
    with pytest.raises(TypeError, match="OrderSide"):
        Fill(
            "AAPL",
            "BUY",
            1,
            100,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commission", -1.0),
        ("slippage_cost", -1.0),
    ],
)
def test_fill_rejects_negative_costs(field, value):
    kwargs = {
        "symbol": "AAPL",
        "side": OrderSide.BUY,
        "quantity": 1,
        "price": 100,
        field: value,
    }

    with pytest.raises(ValueError, match="negative"):
        Fill(**kwargs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commission", "1"),
        ("slippage_cost", True),
    ],
)
def test_fill_rejects_non_numeric_costs(field, value):
    kwargs = {
        "symbol": "AAPL",
        "side": OrderSide.BUY,
        "quantity": 1,
        "price": 100,
        field: value,
    }

    with pytest.raises(TypeError, match="numeric"):
        Fill(**kwargs)


def test_fill_rejects_non_finite_cost():
    with pytest.raises(ValueError, match="finite"):
        Fill(
            "AAPL",
            OrderSide.BUY,
            1,
            100,
            commission=np.inf,
        )


def test_position_rejects_fill_for_other_symbol():
    position = Position("AAPL")

    fill = Fill(
        "MSFT",
        OrderSide.BUY,
        1,
        100,
    )

    with pytest.raises(ValueError, match="symbol"):
        position.apply_fill(fill)


def test_adding_to_long_position_updates_average_price():
    position = Position("AAPL")

    position.apply_fill(Fill("AAPL", OrderSide.BUY, 10, 100))

    position.apply_fill(Fill("AAPL", OrderSide.BUY, 10, 120))

    assert position.quantity == pytest.approx(20)
    assert position.average_price == pytest.approx(110)


def test_adding_to_short_position_updates_average_price():
    position = Position("AAPL")

    position.apply_fill(Fill("AAPL", OrderSide.SELL, 10, 100))

    position.apply_fill(Fill("AAPL", OrderSide.SELL, 10, 80))

    assert position.quantity == pytest.approx(-20)
    assert position.average_price == pytest.approx(90)


def test_partial_long_close_realizes_profit():
    position = Position("AAPL")

    position.apply_fill(Fill("AAPL", OrderSide.BUY, 10, 100))

    position.apply_fill(Fill("AAPL", OrderSide.SELL, 4, 110))

    assert position.quantity == pytest.approx(6)
    assert position.average_price == pytest.approx(100)
    assert position.realized_pnl == pytest.approx(40)


def test_partial_short_close_realizes_profit():
    position = Position("AAPL")

    position.apply_fill(Fill("AAPL", OrderSide.SELL, 10, 100))

    position.apply_fill(Fill("AAPL", OrderSide.BUY, 4, 90))

    assert position.quantity == pytest.approx(-6)
    assert position.realized_pnl == pytest.approx(40)


@pytest.mark.parametrize("price", [0, -1])
def test_position_mark_rejects_invalid_price(price):
    position = Position("AAPL")

    with pytest.raises(ValueError, match="greater than zero"):
        position.mark(price)
