import pandas as pd
import pytest

from trading_engine.regime import (
    MomentumRegime,
    classify_momentum_regime,
    rolling_momentum,
    rolling_momentum_regime,
)


def prices(values):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def test_positive_momentum():
    assert (
        classify_momentum_regime(
            0.10,
            threshold=0.02,
        )
        is MomentumRegime.POSITIVE
    )


def test_negative_momentum():
    assert (
        classify_momentum_regime(
            -0.10,
            threshold=0.02,
        )
        is MomentumRegime.NEGATIVE
    )


def test_neutral_momentum():
    assert (
        classify_momentum_regime(
            0.01,
            threshold=0.02,
        )
        is MomentumRegime.NEUTRAL
    )


def test_rolling_momentum():
    result = rolling_momentum(
        prices(
            [
                100,
                110,
                121,
            ]
        ),
        lookback=1,
    )

    assert result.iloc[0] != result.iloc[0]

    assert result.iloc[1] == pytest.approx(0.10)


@pytest.mark.parametrize(
    "lookback",
    [
        True,
        1.5,
        "5",
    ],
)
def test_lookback_requires_integer(
    lookback,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_momentum(
            prices([100, 101]),
            lookback=lookback,
        )


def test_non_positive_lookback_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        rolling_momentum(
            prices([100, 101]),
            lookback=0,
        )


def test_negative_threshold_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        classify_momentum_regime(
            0.1,
            threshold=-0.01,
        )


def test_rolling_momentum_regime():
    result = rolling_momentum_regime(
        prices(
            [
                100,
                103,
                106,
                100,
                95,
            ]
        ),
        lookback=1,
        threshold=0.02,
    )

    assert result.iloc[0] is pd.NA

    assert set(result.dropna().unique()).issubset(
        {
            "positive",
            "neutral",
            "negative",
        }
    )
