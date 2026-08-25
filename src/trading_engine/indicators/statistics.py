from __future__ import annotations

import pandas as pd

from trading_engine.indicators._validation import (
    validate_numeric_series,
    validate_pair,
    validate_window,
)


def rolling_mean(
    series: pd.Series,
    window: int,
    *,
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate a rolling arithmetic mean.

    Args:
        series: Numeric time series.
        window: Rolling window size.
        min_periods: Minimum observations required to produce a value.
            Defaults to ``window``.

    Returns:
        Rolling mean with the original index preserved.
    """
    validate_numeric_series(
        series,
        name="Series",
        allow_nan=True,
    )
    validate_window(window)

    if min_periods is None:
        min_periods = window
    else:
        validate_window(min_periods, name="min_periods")

    if min_periods > window:
        raise ValueError("min_periods cannot exceed window.")

    result = series.rolling(
        window=window,
        min_periods=min_periods,
    ).mean()

    result.name = "rolling_mean"

    return result


def rolling_std(
    series: pd.Series,
    window: int,
    *,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate rolling standard deviation.

    Args:
        series: Numeric time series.
        window: Rolling window size.
        min_periods: Minimum observations required to produce a value.
            Defaults to ``window``.
        ddof: Delta degrees of freedom used by the variance estimator.

    Returns:
        Rolling standard deviation with the original index preserved.
    """
    validate_numeric_series(
        series,
        name="Series",
        allow_nan=True,
    )
    validate_window(window)

    if min_periods is None:
        min_periods = window
    else:
        validate_window(min_periods, name="min_periods")

    if min_periods > window:
        raise ValueError("min_periods cannot exceed window.")

    if isinstance(ddof, bool) or not isinstance(ddof, int):
        raise TypeError("ddof must be an integer.")

    if ddof < 0:
        raise ValueError("ddof cannot be negative.")

    result = series.rolling(
        window=window,
        min_periods=min_periods,
    ).std(ddof=ddof)

    result.name = "rolling_std"

    return result


def rolling_zscore(
    series: pd.Series,
    window: int,
    *,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate a rolling z-score.

    Z_t = (X_t - rolling_mean_t) / rolling_std_t

    Args:
        series: Numeric time series.
        window: Rolling window size.
        min_periods: Minimum observations required to produce a value.
            Defaults to ``window``.
        ddof: Delta degrees of freedom used by the rolling standard deviation.

    Returns:
        Rolling z-score with the original index preserved.

    Notes:
        If rolling standard deviation is zero, the z-score is undefined
        and NaN is returned for that observation.
    """
    mean = rolling_mean(
        series,
        window,
        min_periods=min_periods,
    )

    std = rolling_std(
        series,
        window,
        min_periods=min_periods,
        ddof=ddof,
    )

    result = (series - mean) / std
    result = result.mask(std == 0)
    result.name = "rolling_zscore"

    return result


def rolling_covariance(
    left: pd.Series,
    right: pd.Series,
    window: int,
    *,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate rolling covariance between two aligned time series.

    Args:
        left: First numeric time series.
        right: Second numeric time series.
        window: Rolling window size.
        min_periods: Minimum paired observations required to produce a value.
            Defaults to ``window``.
        ddof: Delta degrees of freedom used by the covariance estimator.

    Returns:
        Rolling covariance with the original index preserved.
    """
    validate_pair(
        left,
        right,
        allow_nan=True,
    )
    validate_window(window)

    if min_periods is None:
        min_periods = window
    else:
        validate_window(min_periods, name="min_periods")

    if min_periods > window:
        raise ValueError("min_periods cannot exceed window.")

    if isinstance(ddof, bool) or not isinstance(ddof, int):
        raise TypeError("ddof must be an integer.")

    if ddof < 0:
        raise ValueError("ddof cannot be negative.")

    result = left.rolling(
        window=window,
        min_periods=min_periods,
    ).cov(right, ddof=ddof)

    result.name = "rolling_covariance"

    return result


def rolling_correlation(
    left: pd.Series,
    right: pd.Series,
    window: int,
    *,
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate rolling Pearson correlation between two aligned series.

    Args:
        left: First numeric time series.
        right: Second numeric time series.
        window: Rolling window size.
        min_periods: Minimum paired observations required to produce a value.
            Defaults to ``window``.

    Returns:
        Rolling Pearson correlation with the original index preserved.

    Notes:
        Correlation is undefined when either series has zero variance within
        a rolling window. Pandas represents those observations as NaN.
    """
    validate_pair(
        left,
        right,
        allow_nan=True,
    )
    validate_window(window)

    if min_periods is None:
        min_periods = window
    else:
        validate_window(min_periods, name="min_periods")

    if min_periods > window:
        raise ValueError("min_periods cannot exceed window.")

    result = left.rolling(
        window=window,
        min_periods=min_periods,
    ).corr(right)

    result.name = "rolling_correlation"

    return result
