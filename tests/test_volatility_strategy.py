from datetime import UTC, datetime

import pytest

from trading_engine.strategies import (
    SignalDirection,
    StrategyConfig,
    VolatilityBreakoutStrategy,
)


def timestamp(day: int):
    return datetime(
        2026,
        1,
        day,
        tzinfo=UTC,
    )


def test_volatility_breakout_warms_up():
    strategy = VolatilityBreakoutStrategy(
        symbol="AAPL",
        lookback=3,
    )

    signal = strategy.update(
        price=100,
        timestamp=timestamp(1),
    )

    assert signal.direction is SignalDirection.FLAT


def test_upside_breakout_generates_long():
    strategy = VolatilityBreakoutStrategy(
        symbol="AAPL",
        lookback=3,
        breakout_multiplier=2.0,
    )

    prices = [
        100,
        101,
        102,
        103,
        120,
    ]

    signal = None

    for day, price in enumerate(
        prices,
        start=1,
    ):
        signal = strategy.update(
            price=price,
            timestamp=timestamp(day),
        )

    assert signal is not None
    assert signal.direction is SignalDirection.LONG


def test_downside_breakout_generates_short():
    strategy = VolatilityBreakoutStrategy(
        symbol="AAPL",
        lookback=3,
        breakout_multiplier=2.0,
        config=StrategyConfig(
            allow_short=True,
        ),
    )

    prices = [
        100,
        101,
        102,
        103,
        80,
    ]

    signal = None

    for day, price in enumerate(
        prices,
        start=1,
    ):
        signal = strategy.update(
            price=price,
            timestamp=timestamp(day),
        )

    assert signal is not None
    assert signal.direction is SignalDirection.SHORT


def test_downside_breakout_is_flat_without_shorting():
    strategy = VolatilityBreakoutStrategy(
        symbol="AAPL",
        lookback=3,
        breakout_multiplier=2.0,
    )

    prices = [
        100,
        101,
        102,
        103,
        80,
    ]

    signal = None

    for day, price in enumerate(
        prices,
        start=1,
    ):
        signal = strategy.update(
            price=price,
            timestamp=timestamp(day),
        )

    assert signal is not None
    assert signal.direction is SignalDirection.FLAT


def test_large_signal_threshold_can_suppress_breakout():
    strategy = VolatilityBreakoutStrategy(
        symbol="AAPL",
        lookback=3,
        breakout_multiplier=1.0,
        config=StrategyConfig(
            signal_threshold=0.50,
        ),
    )

    prices = [
        100,
        101,
        102,
        103,
        120,
    ]

    signal = None

    for day, price in enumerate(
        prices,
        start=1,
    ):
        signal = strategy.update(
            price=price,
            timestamp=timestamp(day),
        )

    assert signal is not None
    assert signal.direction is SignalDirection.FLAT


def test_invalid_breakout_multiplier_is_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        VolatilityBreakoutStrategy(
            symbol="AAPL",
            breakout_multiplier=0,
        )
