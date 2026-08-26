import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    RegimePerformance,
    regime_performance,
    regime_return_table,
)


def returns():
    return pd.Series(
        [
            0.01,
            0.02,
            -0.01,
            0.03,
        ],
        index=pd.date_range(
            "2026-01-01",
            periods=4,
            freq="D",
        ),
        dtype=float,
    )


def regimes():
    return pd.Series(
        [
            "bull",
            "bull",
            "bear",
            "bear",
        ],
        index=returns().index,
        dtype=object,
    )


def test_regime_performance():
    result = regime_performance(
        returns(),
        regimes(),
    )

    assert len(result) == 2

    assert isinstance(
        result[0],
        RegimePerformance,
    )


def test_regime_return_table():
    result = regime_return_table(
        returns(),
        regimes(),
    )

    assert {
        "regime",
        "observations",
        "average_return",
        "cumulative_return",
        "volatility",
        "win_rate",
    } == set(result.columns)


def test_single_observation_regime_has_zero_volatility():
    values = pd.Series(
        [
            0.01,
        ]
    )

    labels = pd.Series(
        [
            "bull",
        ]
    )

    result = regime_performance(
        values,
        labels,
    )

    assert result[0].volatility == 0.0


def test_returns_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        regime_performance(
            [],
            regimes(),
        )


def test_regimes_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        regime_performance(
            returns(),
            [],
        )


def test_empty_returns_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        regime_performance(
            pd.Series(dtype=float),
            pd.Series(dtype=object),
        )


def test_indexes_must_match():
    with pytest.raises(
        ValueError,
        match="indexes",
    ):
        regime_performance(
            returns(),
            regimes().reset_index(drop=True),
        )


def test_non_finite_returns_rejected():
    values = returns()

    values.iloc[0] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        regime_performance(
            values,
            regimes(),
        )


def test_missing_regime_is_ignored():
    labels = regimes()

    labels.iloc[0] = pd.NA

    result = regime_performance(
        returns(),
        labels,
    )

    assert sum(item.observations for item in result) == 3
