from datetime import UTC, datetime

import numpy as np
import pytest

from trading_engine.strategies.signals import (
    SignalDirection,
    StrategySignal,
)


def make_timestamp():
    return datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )


def test_signal_normalizes_symbol():
    signal = StrategySignal(
        symbol=" aapl ",
        direction=SignalDirection.LONG,
        timestamp=make_timestamp(),
    )

    assert signal.symbol == "AAPL"


def test_long_signed_strength_is_positive():
    signal = StrategySignal(
        "AAPL",
        SignalDirection.LONG,
        make_timestamp(),
        strength=0.8,
    )

    assert signal.signed_strength == pytest.approx(0.8)


def test_short_signed_strength_is_negative():
    signal = StrategySignal(
        "AAPL",
        SignalDirection.SHORT,
        make_timestamp(),
        strength=0.8,
    )

    assert signal.signed_strength == pytest.approx(-0.8)


def test_flat_signed_strength_is_zero():
    signal = StrategySignal(
        "AAPL",
        SignalDirection.FLAT,
        make_timestamp(),
        strength=0.8,
    )

    assert signal.signed_strength == pytest.approx(0.0)


@pytest.mark.parametrize("strength", [0.0, 0.5, 1.0])
def test_valid_strengths_are_accepted(strength):
    StrategySignal(
        "AAPL",
        SignalDirection.LONG,
        make_timestamp(),
        strength=strength,
    )


@pytest.mark.parametrize("strength", [-0.1, 1.1])
def test_strength_outside_unit_interval_is_rejected(
    strength,
):
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        StrategySignal(
            "AAPL",
            SignalDirection.LONG,
            make_timestamp(),
            strength=strength,
        )


@pytest.mark.parametrize(
    "strength",
    ["1", True],
)
def test_non_numeric_strength_is_rejected(strength):
    with pytest.raises(TypeError, match="numeric"):
        StrategySignal(
            "AAPL",
            SignalDirection.LONG,
            make_timestamp(),
            strength=strength,
        )


def test_non_finite_strength_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        StrategySignal(
            "AAPL",
            SignalDirection.LONG,
            make_timestamp(),
            strength=np.inf,
        )


def test_empty_symbol_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        StrategySignal(
            " ",
            SignalDirection.LONG,
            make_timestamp(),
        )


def test_invalid_direction_is_rejected():
    with pytest.raises(
        TypeError,
        match="SignalDirection",
    ):
        StrategySignal(
            "AAPL",
            "LONG",
            make_timestamp(),
        )


def test_invalid_timestamp_is_rejected():
    with pytest.raises(TypeError, match="datetime"):
        StrategySignal(
            "AAPL",
            SignalDirection.LONG,
            "2026-01-01",
        )
