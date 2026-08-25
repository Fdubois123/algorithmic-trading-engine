import numpy as np
import pandas as pd
import pytest

from trading_engine.indicators.statistics import (
    rolling_mean,
    rolling_std,
)


@pytest.fixture
def series():
    return pd.Series(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        index=pd.date_range("2026-01-01", periods=5),
    )


def test_rolling_mean_is_correct(series):
    result = rolling_mean(series, window=3)

    expected = pd.Series(
        [np.nan, np.nan, 2.0, 3.0, 4.0],
        index=series.index,
        name="rolling_mean",
    )

    pd.testing.assert_series_equal(result, expected)


def test_rolling_std_is_correct(series):
    result = rolling_std(series, window=3)

    expected = pd.Series(
        [np.nan, np.nan, 1.0, 1.0, 1.0],
        index=series.index,
        name="rolling_std",
    )

    pd.testing.assert_series_equal(result, expected)


def test_rolling_mean_preserves_index(series):
    result = rolling_mean(series, window=3)

    pd.testing.assert_index_equal(result.index, series.index)


def test_rolling_std_preserves_index(series):
    result = rolling_std(series, window=3)

    pd.testing.assert_index_equal(result.index, series.index)


def test_min_periods_allows_earlier_values(series):
    result = rolling_mean(
        series,
        window=3,
        min_periods=1,
    )

    assert result.iloc[0] == pytest.approx(1.0)
    assert result.iloc[1] == pytest.approx(1.5)
    assert result.iloc[2] == pytest.approx(2.0)


def test_ddof_zero_uses_population_standard_deviation():
    series = pd.Series([1.0, 2.0, 3.0])

    result = rolling_std(
        series,
        window=3,
        ddof=0,
    )

    expected = np.std([1.0, 2.0, 3.0], ddof=0)

    assert result.iloc[-1] == pytest.approx(expected)


def test_constant_series_has_zero_standard_deviation():
    series = pd.Series([5.0, 5.0, 5.0, 5.0])

    result = rolling_std(
        series,
        window=3,
    )

    assert result.iloc[-1] == pytest.approx(0.0)


def test_nan_is_handled_with_min_periods():
    series = pd.Series([1.0, np.nan, 3.0])

    result = rolling_mean(
        series,
        window=3,
        min_periods=2,
    )

    assert result.iloc[-1] == pytest.approx(2.0)


def test_min_periods_greater_than_window_raises_error(series):
    with pytest.raises(
        ValueError,
        match="cannot exceed window",
    ):
        rolling_mean(
            series,
            window=3,
            min_periods=4,
        )


@pytest.mark.parametrize("window", [0, -1])
def test_invalid_window_raises_error(series, window):
    with pytest.raises(ValueError, match="greater than zero"):
        rolling_mean(series, window=window)


@pytest.mark.parametrize("ddof", [-1, -5])
def test_negative_ddof_raises_error(series, ddof):
    with pytest.raises(ValueError, match="cannot be negative"):
        rolling_std(
            series,
            window=3,
            ddof=ddof,
        )


@pytest.mark.parametrize("ddof", [1.5, "1", True])
def test_non_integer_ddof_raises_error(series, ddof):
    with pytest.raises(TypeError, match="integer"):
        rolling_std(
            series,
            window=3,
            ddof=ddof,
        )
