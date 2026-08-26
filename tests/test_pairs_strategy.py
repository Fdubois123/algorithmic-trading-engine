import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    PairPosition,
    PairSignal,
    PairsTradingStrategy,
    generate_pair_positions,
)


def test_strategy_starts_flat():
    strategy = PairsTradingStrategy()

    assert strategy.position is PairPosition.FLAT


def test_negative_entry_creates_long_spread():
    strategy = PairsTradingStrategy(
        entry_z=2.0,
        exit_z=0.5,
    )

    signal = strategy.update(-2.1)

    assert isinstance(
        signal,
        PairSignal,
    )

    assert signal.position is PairPosition.LONG_SPREAD

    assert signal.changed


def test_positive_entry_creates_short_spread():
    strategy = PairsTradingStrategy()

    signal = strategy.update(2.1)

    assert signal.position is PairPosition.SHORT_SPREAD

    assert signal.changed


def test_long_spread_remains_open():
    strategy = PairsTradingStrategy()

    strategy.update(-2.5)

    signal = strategy.update(-1.0)

    assert signal.position is PairPosition.LONG_SPREAD

    assert not signal.changed


def test_long_spread_exits_on_mean_reversion():
    strategy = PairsTradingStrategy(
        exit_z=0.5,
    )

    strategy.update(-2.5)

    signal = strategy.update(-0.4)

    assert signal.position is PairPosition.FLAT
    assert signal.changed


def test_short_spread_exits_on_mean_reversion():
    strategy = PairsTradingStrategy(
        exit_z=0.5,
    )

    strategy.update(2.5)

    signal = strategy.update(0.4)

    assert signal.position is PairPosition.FLAT


def test_long_spread_stop_loss():
    strategy = PairsTradingStrategy(
        entry_z=2.0,
        stop_z=3.0,
    )

    strategy.update(-2.1)

    signal = strategy.update(-3.1)

    assert signal.position is PairPosition.FLAT


def test_short_spread_stop_loss():
    strategy = PairsTradingStrategy(
        entry_z=2.0,
        stop_z=3.0,
    )

    strategy.update(2.1)

    signal = strategy.update(3.1)

    assert signal.position is PairPosition.FLAT


def test_stop_can_be_disabled():
    strategy = PairsTradingStrategy(
        entry_z=2.0,
        stop_z=None,
    )

    strategy.update(-2.1)

    signal = strategy.update(-10.0)

    assert signal.position is PairPosition.LONG_SPREAD


def test_reset_returns_strategy_to_flat():
    strategy = PairsTradingStrategy()

    strategy.update(2.5)
    strategy.reset()

    assert strategy.position is PairPosition.FLAT


@pytest.mark.parametrize(
    "value",
    [
        True,
        "2",
    ],
)
def test_entry_z_must_be_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        PairsTradingStrategy(entry_z=value)


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        np.inf,
    ],
)
def test_entry_z_must_be_positive_finite(
    value,
):
    with pytest.raises(ValueError):
        PairsTradingStrategy(entry_z=value)


def test_exit_must_be_below_entry():
    with pytest.raises(
        ValueError,
        match="smaller",
    ):
        PairsTradingStrategy(
            entry_z=2.0,
            exit_z=2.0,
        )


def test_stop_must_exceed_entry():
    with pytest.raises(
        ValueError,
        match="greater",
    ):
        PairsTradingStrategy(
            entry_z=2.0,
            stop_z=2.0,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "1",
    ],
)
def test_update_requires_numeric_zscore(
    value,
):
    strategy = PairsTradingStrategy()

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        strategy.update(value)


def test_update_rejects_non_finite_zscore():
    strategy = PairsTradingStrategy()

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        strategy.update(np.inf)


def test_generate_pair_positions():
    index = pd.date_range(
        "2026-01-01",
        periods=10,
        freq="D",
    )

    spread = pd.Series(
        [
            0.0,
            0.1,
            -0.1,
            0.0,
            0.1,
            5.0,
            0.0,
            -5.0,
            0.0,
            0.1,
        ],
        index=index,
    )

    result = generate_pair_positions(
        spread,
        window=3,
        entry_z=1.0,
        exit_z=0.2,
        stop_z=3.0,
    )

    assert len(result) == len(spread)
    assert result.name == "pair_position"

    assert set(result.unique()).issubset(
        {
            "flat",
            "long_spread",
            "short_spread",
        }
    )
