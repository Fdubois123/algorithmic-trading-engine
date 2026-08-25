from __future__ import annotations

import numpy as np
import pandas as pd

from trading_engine.indicators._validation import (
    validate_numeric_series,
    validate_positive_series,
    validate_window,
)
from trading_engine.indicators.returns import log_returns
from trading_engine.indicators.statistics import rolling_std


def historical_volatility(
    returns: pd.Series,
    window: int,
    *,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate rolling historical volatility from periodic returns."""
    result = rolling_std(
        returns,
        window,
        min_periods=min_periods,
        ddof=ddof,
    )
    result.name = "historical_volatility"

    return result


def annualized_volatility(
    returns: pd.Series,
    window: int,
    *,
    periods_per_year: int = 252,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate annualized rolling historical volatility."""
    validate_window(periods_per_year, name="periods_per_year")

    volatility = historical_volatility(
        returns,
        window,
        min_periods=min_periods,
        ddof=ddof,
    )

    result = volatility * np.sqrt(periods_per_year)
    result.name = "annualized_volatility"

    return result


def downside_volatility(
    returns: pd.Series,
    window: int,
    *,
    target_return: float = 0.0,
    periods_per_year: int | None = None,
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate rolling downside deviation relative to a target return."""
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    validate_window(window)

    if not isinstance(target_return, (int, float)) or isinstance(
        target_return,
        bool,
    ):
        raise TypeError("target_return must be numeric.")

    if not np.isfinite(float(target_return)):
        raise ValueError("target_return must be finite.")

    if min_periods is None:
        min_periods = window
    else:
        validate_window(min_periods, name="min_periods")

    if min_periods > window:
        raise ValueError("min_periods cannot exceed window.")

    downside = np.minimum(returns - target_return, 0.0)

    result = (
        downside.pow(2)
        .rolling(
            window=window,
            min_periods=min_periods,
        )
        .mean()
        .pow(0.5)
    )

    if periods_per_year is not None:
        validate_window(periods_per_year, name="periods_per_year")
        result = result * np.sqrt(periods_per_year)

    result.name = "downside_volatility"

    return result


def ewma_volatility(
    returns: pd.Series,
    *,
    span: int = 20,
    periods_per_year: int | None = None,
    min_periods: int = 1,
) -> pd.Series:
    """Calculate exponentially weighted volatility."""
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    validate_window(span, name="span")
    validate_window(min_periods, name="min_periods")

    result = returns.ewm(
        span=span,
        adjust=False,
        min_periods=min_periods,
    ).std(bias=False)

    if periods_per_year is not None:
        validate_window(periods_per_year, name="periods_per_year")
        result = result * np.sqrt(periods_per_year)

    result.name = "ewma_volatility"

    return result


def parkinson_volatility(
    high: pd.Series,
    low: pd.Series,
    window: int,
    *,
    periods_per_year: int | None = None,
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate Parkinson range-based volatility estimator."""
    validate_positive_series(high, name="High")
    validate_positive_series(low, name="Low")

    if not high.index.equals(low.index):
        raise ValueError("High and low indices must match exactly.")

    if (high < low).any():
        raise ValueError("High prices cannot be lower than low prices.")

    validate_window(window)

    if min_periods is None:
        min_periods = window
    else:
        validate_window(min_periods, name="min_periods")

    if min_periods > window:
        raise ValueError("min_periods cannot exceed window.")

    log_range_squared = np.log(high / low).pow(2)

    rolling_mean = log_range_squared.rolling(
        window=window,
        min_periods=min_periods,
    ).mean()

    result = np.sqrt(
        rolling_mean / (4.0 * np.log(2.0)),
    )

    if periods_per_year is not None:
        validate_window(periods_per_year, name="periods_per_year")
        result = result * np.sqrt(periods_per_year)

    result.name = "parkinson_volatility"

    return result


def close_to_close_volatility(
    prices: pd.Series,
    window: int,
    *,
    periods_per_year: int | None = None,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate volatility directly from a positive price series."""
    validate_positive_series(prices, name="Prices")

    returns = log_returns(prices)

    result = rolling_std(
        returns,
        window,
        min_periods=min_periods,
        ddof=ddof,
    )

    if periods_per_year is not None:
        validate_window(periods_per_year, name="periods_per_year")
        result = result * np.sqrt(periods_per_year)

    result.name = "close_to_close_volatility"

    return result
