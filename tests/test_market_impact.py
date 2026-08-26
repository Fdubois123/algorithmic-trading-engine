import pytest

from trading_engine.backtest.models import (
    OrderSide,
)
from trading_engine.execution import (
    SquareRootMarketImpact,
)


def test_market_impact_increases_with_participation():
    model = SquareRootMarketImpact(
        coefficient_bps=100,
    )

    small = model.impact_bps(
        quantity=1_000,
        volume=100_000,
    )

    large = model.impact_bps(
        quantity=10_000,
        volume=100_000,
    )

    assert large > small


def test_buy_market_impact_is_adverse():
    model = SquareRootMarketImpact(
        coefficient_bps=100,
    )

    result = model.adjust(
        market_price=100,
        side=OrderSide.BUY,
        quantity=10_000,
        volume=100_000,
    )

    assert result > 100


def test_sell_market_impact_is_adverse():
    model = SquareRootMarketImpact(
        coefficient_bps=100,
    )

    result = model.adjust(
        market_price=100,
        side=OrderSide.SELL,
        quantity=10_000,
        volume=100_000,
    )

    assert result < 100


def test_market_impact_respects_cap():
    model = SquareRootMarketImpact(
        coefficient_bps=1_000,
        max_impact_bps=50,
    )

    result = model.impact_bps(
        quantity=100_000,
        volume=100_000,
    )

    assert result == pytest.approx(50)


def test_invalid_quantity_is_rejected():
    model = SquareRootMarketImpact()

    with pytest.raises(
        ValueError,
        match="quantity",
    ):
        model.impact_bps(
            quantity=0,
            volume=100_000,
        )
