import pytest

from trading_engine.backtest.models import (
    OrderSide,
)
from trading_engine.execution import (
    BidAskSpreadModel,
    ConstantBpsSlippage,
    NoSlippage,
)


def test_no_slippage_preserves_price():
    model = NoSlippage()

    result = model.adjust(
        market_price=100,
        side=OrderSide.BUY,
    )

    assert result == pytest.approx(100)


def test_buy_slippage_increases_price():
    model = ConstantBpsSlippage(
        bps=10,
    )

    result = model.adjust(
        market_price=100,
        side=OrderSide.BUY,
    )

    assert result == pytest.approx(100.10)


def test_sell_slippage_reduces_price():
    model = ConstantBpsSlippage(
        bps=10,
    )

    result = model.adjust(
        market_price=100,
        side=OrderSide.SELL,
    )

    assert result == pytest.approx(99.90)


def test_spread_is_adverse_for_buy():
    model = BidAskSpreadModel(
        half_spread_bps=5,
    )

    result = model.adjust(
        market_price=100,
        side=OrderSide.BUY,
    )

    assert result == pytest.approx(100.05)


def test_spread_is_adverse_for_sell():
    model = BidAskSpreadModel(
        half_spread_bps=5,
    )

    result = model.adjust(
        market_price=100,
        side=OrderSide.SELL,
    )

    assert result == pytest.approx(99.95)


def test_negative_slippage_is_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        ConstantBpsSlippage(
            bps=-1,
        )
