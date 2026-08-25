import pytest

from trading_engine.backtest.models import (
    Fill,
    Order,
    OrderSide,
)
from trading_engine.backtest.portfolio import (
    Portfolio,
)


def test_initial_equity_equals_cash():
    portfolio = Portfolio(100_000)

    assert portfolio.equity == pytest.approx(100_000)


def test_buy_reduces_cash():
    portfolio = Portfolio(100_000)

    portfolio.process_fill(
        Fill(
            "AAPL",
            OrderSide.BUY,
            10,
            100,
        )
    )

    assert portfolio.cash == pytest.approx(99_000)


def test_sell_increases_cash():
    portfolio = Portfolio(
        100_000,
        allow_short=True,
    )

    portfolio.process_fill(
        Fill(
            "AAPL",
            OrderSide.SELL,
            10,
            100,
        )
    )

    assert portfolio.cash == pytest.approx(101_000)


def test_commission_reduces_cash():
    portfolio = Portfolio(100_000)

    portfolio.process_fill(
        Fill(
            "AAPL",
            OrderSide.BUY,
            10,
            100,
            commission=5,
        )
    )

    assert portfolio.cash == pytest.approx(98_995)


def test_insufficient_cash_rejected():
    portfolio = Portfolio(100)

    order = Order(
        "AAPL",
        OrderSide.BUY,
        10,
    )

    with pytest.raises(
        ValueError,
        match="Insufficient",
    ):
        portfolio.validate_order(
            order,
            100,
        )


def test_short_position_rejected_by_default():
    portfolio = Portfolio(100_000)

    order = Order(
        "AAPL",
        OrderSide.SELL,
        1,
    )

    with pytest.raises(
        ValueError,
        match="short",
    ):
        portfolio.validate_order(
            order,
            100,
        )


def test_short_allowed_when_enabled():
    portfolio = Portfolio(
        100_000,
        allow_short=True,
    )

    order = Order(
        "AAPL",
        OrderSide.SELL,
        1,
    )

    portfolio.validate_order(
        order,
        100,
    )
