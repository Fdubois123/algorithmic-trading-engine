from datetime import UTC, datetime

import pytest

from trading_engine.strategies import (
    SignalDirection,
    StrategyConfig,
    ZScoreMeanReversionStrategy,
)


def timestamp(day: int):
    return datetime(
        2026,
        1,
        day,
        tzinfo=UTC,
    )


def test_mean_reversion_is_flat_during_warmup():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
    )

    signal = strategy.update(
        price=100,
        timestamp=timestamp(1),
    )

    assert signal.direction is SignalDirection.FLAT


def test_downside_deviation_enters_long():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
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

    assert signal.direction is SignalDirection.LONG


def test_long_position_exits_after_reversion():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
    )

    strategy.update(
        price=100,
        timestamp=timestamp(1),
    )
    strategy.update(
        price=100,
        timestamp=timestamp(2),
    )
    strategy.update(
        price=90,
        timestamp=timestamp(3),
    )

    signal = strategy.update(
        price=100,
        timestamp=timestamp(4),
    )

    assert signal.direction is SignalDirection.FLAT


def test_upside_deviation_enters_short():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
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
        price=110,
        timestamp=timestamp(3),
    )

    assert signal.direction is SignalDirection.SHORT


def test_constant_prices_remain_flat():
    strategy = ZScoreMeanReversionStrategy(
        symbol="AAPL",
        window=3,
        entry_z=1.0,
        exit_z=0.25,
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
        price=100,
        timestamp=timestamp(3),
    )

    assert signal.direction is SignalDirection.FLAT


def test_exit_z_must_be_below_entry_z():
    with pytest.raises(
        ValueError,
        match="smaller",
    ):
        ZScoreMeanReversionStrategy(
            symbol="AAPL",
            window=10,
            entry_z=1.0,
            exit_z=1.0,
        )
