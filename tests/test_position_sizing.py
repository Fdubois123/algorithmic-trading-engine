from datetime import UTC, datetime

import numpy as np
import pytest

from trading_engine.strategies.signals import (
    SignalDirection,
    StrategySignal,
)
from trading_engine.strategies.sizing import (
    FixedFractionSizer,
    PositionSizer,
    VolatilityTargetSizer,
)


def make_signal(
    direction=SignalDirection.LONG,
    strength=1.0,
):
    return StrategySignal(
        symbol="AAPL",
        direction=direction,
        timestamp=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
        strength=strength,
    )


def test_fixed_fraction_long_quantity():
    sizer = FixedFractionSizer(
        fraction=0.10,
    )

    quantity = sizer.size(
        signal=make_signal(),
        equity=100_000,
        price=100,
    )

    assert quantity == pytest.approx(100)


def test_fixed_fraction_short_quantity_is_negative():
    sizer = FixedFractionSizer(
        fraction=0.10,
    )

    quantity = sizer.size(
        signal=make_signal(SignalDirection.SHORT),
        equity=100_000,
        price=100,
    )

    assert quantity == pytest.approx(-100)


def test_flat_signal_returns_zero_quantity():
    sizer = FixedFractionSizer()

    quantity = sizer.size(
        signal=make_signal(SignalDirection.FLAT),
        equity=100_000,
        price=100,
    )

    assert quantity == pytest.approx(0)


def test_signal_strength_scales_position():
    sizer = FixedFractionSizer(
        fraction=0.20,
    )

    quantity = sizer.size(
        signal=make_signal(
            strength=0.5,
        ),
        equity=100_000,
        price=100,
    )

    assert quantity == pytest.approx(100)


@pytest.mark.parametrize("fraction", [0, -0.1, 1.1])
def test_invalid_fixed_fraction_is_rejected(fraction):
    with pytest.raises(ValueError):
        FixedFractionSizer(
            fraction=fraction,
        )


def test_volatility_target_multiplier():
    sizer = VolatilityTargetSizer(
        target_volatility=0.10,
        forecast_volatility=0.20,
        max_leverage=1.0,
    )

    assert sizer.exposure_multiplier == pytest.approx(0.5)


def test_volatility_target_is_capped_by_leverage():
    sizer = VolatilityTargetSizer(
        target_volatility=0.20,
        forecast_volatility=0.05,
        max_leverage=1.5,
    )

    assert sizer.exposure_multiplier == pytest.approx(1.5)


def test_volatility_target_long_quantity():
    sizer = VolatilityTargetSizer(
        target_volatility=0.10,
        forecast_volatility=0.20,
    )

    quantity = sizer.size(
        signal=make_signal(),
        equity=100_000,
        price=100,
    )

    assert quantity == pytest.approx(500)


def test_volatility_target_short_quantity():
    sizer = VolatilityTargetSizer(
        target_volatility=0.10,
        forecast_volatility=0.20,
    )

    quantity = sizer.size(
        signal=make_signal(SignalDirection.SHORT),
        equity=100_000,
        price=100,
    )

    assert quantity == pytest.approx(-500)


@pytest.mark.parametrize(
    ("equity", "price"),
    [
        (0, 100),
        (-1, 100),
        (100_000, 0),
        (100_000, -10),
    ],
)
def test_invalid_equity_or_price_is_rejected(
    equity,
    price,
):
    sizer = FixedFractionSizer()

    with pytest.raises(ValueError):
        sizer.size(
            signal=make_signal(),
            equity=equity,
            price=price,
        )


def test_non_finite_equity_is_rejected():
    sizer = FixedFractionSizer()

    with pytest.raises(ValueError, match="finite"):
        sizer.size(
            signal=make_signal(),
            equity=np.inf,
            price=100,
        )


def test_base_position_sizer_contract():
    class TestSizer(PositionSizer):
        def size(
            self,
            *,
            signal,
            equity,
            price,
        ):
            return super().size(
                signal=signal,
                equity=equity,
                price=price,
            )

    sizer = TestSizer()

    with pytest.raises(NotImplementedError):
        sizer.size(
            signal=make_signal(),
            equity=100_000,
            price=100,
        )
