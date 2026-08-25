import numpy as np
import pandas as pd
import pytest

from trading_engine.indicators._validation import (
    validate_numeric_series,
    validate_pair,
    validate_positive_series,
    validate_window,
)


def test_valid_numeric_series_passes():
    series = pd.Series([1.0, 2.0, 3.0])

    validate_numeric_series(series)


def test_non_series_raises_type_error():
    with pytest.raises(TypeError, match="pandas Series"):
        validate_numeric_series([1.0, 2.0, 3.0])


def test_empty_series_raises_error():
    series = pd.Series(dtype=float)

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_numeric_series(series)


def test_non_numeric_series_raises_error():
    series = pd.Series(["a", "b", "c"])

    with pytest.raises(TypeError, match="numeric"):
        validate_numeric_series(series)


def test_nan_values_raise_error_by_default():
    series = pd.Series([1.0, np.nan, 3.0])

    with pytest.raises(ValueError, match="missing"):
        validate_numeric_series(series)


def test_nan_values_can_be_allowed():
    series = pd.Series([1.0, np.nan, 3.0])

    validate_numeric_series(series, allow_nan=True)


def test_positive_series_accepts_valid_values():
    series = pd.Series([1.0, 2.0, 3.0])

    validate_positive_series(series)


def test_zero_value_is_rejected():
    series = pd.Series([1.0, 0.0, 3.0])

    with pytest.raises(ValueError, match="strictly positive"):
        validate_positive_series(series)


def test_negative_value_is_rejected():
    series = pd.Series([1.0, -2.0, 3.0])

    with pytest.raises(ValueError, match="strictly positive"):
        validate_positive_series(series)


@pytest.mark.parametrize("window", [1, 5, 20, 252])
def test_valid_windows_pass(window):
    validate_window(window)


@pytest.mark.parametrize("window", [0, -1, -20])
def test_non_positive_windows_raise_error(window):
    with pytest.raises(ValueError, match="greater than zero"):
        validate_window(window)


@pytest.mark.parametrize("window", [1.5, "20", None, True])
def test_non_integer_windows_raise_error(window):
    with pytest.raises(TypeError, match="integer"):
        validate_window(window)


def test_valid_pair_passes():
    index = pd.date_range("2026-01-01", periods=3)

    left = pd.Series([1.0, 2.0, 3.0], index=index)
    right = pd.Series([4.0, 5.0, 6.0], index=index)

    validate_pair(left, right)


def test_pair_with_mismatched_indices_raises_error():
    left = pd.Series(
        [1.0, 2.0, 3.0],
        index=pd.date_range("2026-01-01", periods=3),
    )

    right = pd.Series(
        [4.0, 5.0, 6.0],
        index=pd.date_range("2026-01-02", periods=3),
    )

    with pytest.raises(ValueError, match="indices must match"):
        validate_pair(left, right)


def test_pair_rejects_non_numeric_left_series():
    index = pd.date_range("2026-01-01", periods=3)

    left = pd.Series(["a", "b", "c"], index=index)
    right = pd.Series([1.0, 2.0, 3.0], index=index)

    with pytest.raises(TypeError, match="numeric"):
        validate_pair(left, right)


def test_pair_rejects_non_numeric_right_series():
    index = pd.date_range("2026-01-01", periods=3)

    left = pd.Series([1.0, 2.0, 3.0], index=index)
    right = pd.Series(["a", "b", "c"], index=index)

    with pytest.raises(TypeError, match="numeric"):
        validate_pair(left, right)


def test_pair_allows_nan_when_enabled():
    index = pd.date_range("2026-01-01", periods=3)

    left = pd.Series([1.0, np.nan, 3.0], index=index)
    right = pd.Series([4.0, 5.0, np.nan], index=index)

    validate_pair(
        left,
        right,
        allow_nan=True,
    )


def test_pair_rejects_nan_when_disabled():
    index = pd.date_range("2026-01-01", periods=3)

    left = pd.Series([1.0, np.nan, 3.0], index=index)
    right = pd.Series([4.0, 5.0, 6.0], index=index)

    with pytest.raises(ValueError, match="missing"):
        validate_pair(
            left,
            right,
            allow_nan=False,
        )
