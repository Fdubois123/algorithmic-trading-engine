import numpy as np
import pandas as pd
import pytest

from trading_engine.indicators._validation import (
    validate_numeric_series,
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
