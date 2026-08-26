from datetime import UTC, datetime

import pytest

from trading_engine.strategies import (
    SignalDirection,
    StrategyConfig,
    TimeSeriesMomentumStrategy,
)


def timestamp(day: int):
    return datetime(
        2026,
        1,
        day,
        tzinfo=UTC,
    )


def test_momentum_is_flat_during_warmup():
    strategy = TimeSeriesMomentumStrategy(
        symbol="AAPL",
        lookback=2,
    )

    signal = strategy.update(
        price=100,
        timestamp=timestamp(1),
    )

    assert signal.direction is SignalDirection.FLAT


def test_positive_momentum_generates_long():
    strategy = TimeSeriesMomentumStrategy(
        symbol="AAPL",
        lookback=2,
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

    assert signal.direction is SignalDirection.LONG


def test_negative_momentum_generates_short():
    strategy = TimeSeriesMomentumStrategy(
        symbol="AAPL",
        lookback=2,
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
        price=90,
        timestamp=timestamp(3),
    )

    assert signal.direction is SignalDirection.SHORT


def test_negative_momentum_is_flat_without_shorting():
    strategy = TimeSeriesMomentumStrategy(
        symbol="AAPL",
        lookback=2,
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
        price=90,
        timestamp=timestamp(3),
    )

    assert signal.direction is SignalDirection.FLAT


def test_momentum_threshold_suppresses_signal():
    strategy = TimeSeriesMomentumStrategy(
        symbol="AAPL",
        lookback=2,
        config=StrategyConfig(
            signal_threshold=0.20,
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

    assert signal.direction is SignalDirection.FLAT


def test_invalid_lookback_is_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        TimeSeriesMomentumStrategy(
            symbol="AAPL",
            lookback=0,
        )
