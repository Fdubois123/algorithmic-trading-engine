from datetime import UTC, datetime

import pytest

from trading_engine.strategies import (
    MovingAverageTrendStrategy,
    SignalDirection,
    StrategyConfig,
)


def timestamp(day: int):
    return datetime(
        2026,
        1,
        day,
        tzinfo=UTC,
    )


def test_trend_is_flat_during_warmup():
    strategy = MovingAverageTrendStrategy(
        symbol="AAPL",
        fast_window=2,
        slow_window=3,
    )

    signal = strategy.update(
        price=100,
        timestamp=timestamp(1),
    )

    assert signal.direction is SignalDirection.FLAT


def test_positive_trend_generates_long_signal():
    strategy = MovingAverageTrendStrategy(
        symbol="AAPL",
        fast_window=2,
        slow_window=3,
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
    assert signal.strength > 0


def test_negative_trend_generates_short_when_enabled():
    strategy = MovingAverageTrendStrategy(
        symbol="AAPL",
        fast_window=2,
        slow_window=3,
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


def test_negative_trend_is_flat_when_short_disabled():
    strategy = MovingAverageTrendStrategy(
        symbol="AAPL",
        fast_window=2,
        slow_window=3,
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


def test_signal_threshold_suppresses_small_trend():
    strategy = MovingAverageTrendStrategy(
        symbol="AAPL",
        fast_window=2,
        slow_window=3,
        config=StrategyConfig(
            signal_threshold=0.10,
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
        price=101,
        timestamp=timestamp(3),
    )

    assert signal.direction is SignalDirection.FLAT


def test_fast_window_must_be_smaller_than_slow_window():
    with pytest.raises(
        ValueError,
        match="smaller",
    ):
        MovingAverageTrendStrategy(
            symbol="AAPL",
            fast_window=5,
            slow_window=5,
        )
