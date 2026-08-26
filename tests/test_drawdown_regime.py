import numpy as np
import pandas as pd
import pytest

from trading_engine.regime import (
    DrawdownRegime,
    classify_drawdown_regime,
    rolling_drawdown_regime,
    running_drawdown,
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


def test_running_drawdown():
    result = running_drawdown(prices([100, 110, 99]))

    assert result.iloc[0] == pytest.approx(0.0)

    assert result.iloc[1] == pytest.approx(0.0)

    assert result.iloc[2] == pytest.approx(-0.1)


def test_shallow_drawdown():
    assert classify_drawdown_regime(-0.05) is DrawdownRegime.SHALLOW


def test_moderate_drawdown():
    assert classify_drawdown_regime(-0.15) is DrawdownRegime.MODERATE


def test_deep_drawdown():
    assert classify_drawdown_regime(-0.25) is DrawdownRegime.DEEP


def test_positive_drawdown_rejected():
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        classify_drawdown_regime(0.1)


def test_invalid_threshold_order_rejected():
    with pytest.raises(
        ValueError,
        match="smaller",
    ):
        classify_drawdown_regime(
            -0.1,
            moderate_threshold=-0.2,
            deep_threshold=-0.1,
        )


def test_rolling_drawdown_regime():
    result = rolling_drawdown_regime(
        prices(
            [
                100,
                110,
                100,
                90,
                80,
            ]
        )
    )

    assert result.iloc[0] == "shallow"
    assert result.iloc[-1] in {
        "moderate",
        "deep",
    }


def test_non_finite_prices_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        running_drawdown(
            prices(
                [
                    100,
                    np.inf,
                ]
            )
        )
