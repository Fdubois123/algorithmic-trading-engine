from __future__ import annotations

import math

import numpy as np
import pandas as pd

from trading_engine.regime.labels import (
    VolatilityRegime,
)


def _validate_returns(
    returns: pd.Series,
) -> pd.Series:
    if not isinstance(
        returns,
        pd.Series,
    ):
        raise TypeError("returns must be a pandas Series.")

    if returns.empty:
        raise ValueError("returns cannot be empty.")

    try:
        values = returns.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("returns must contain numeric values.") from error

    array = values.to_numpy(dtype=float)

    if not np.isfinite(array).all():
        raise ValueError("returns must contain only finite values.")

    return values


def _validate_window(
    window: int,
) -> int:
    if isinstance(
        window,
        bool,
    ) or not isinstance(
        window,
        int,
    ):
        raise TypeError("window must be an integer.")

    if window < 2:
        raise ValueError("window must be at least 2.")

    return window


def _validate_periods_per_year(
    periods_per_year: int,
) -> int:
    if isinstance(
        periods_per_year,
        bool,
    ) or not isinstance(
        periods_per_year,
        int,
    ):
        raise TypeError("periods_per_year must be an integer.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")

    return periods_per_year


def rolling_realized_volatility(
    returns: pd.Series,
    *,
    window: int = 20,
    periods_per_year: int = 252,
) -> pd.Series:
    """Calculate annualized trailing realized volatility."""
    values = _validate_returns(returns)

    window = _validate_window(window)

    periods_per_year = _validate_periods_per_year(periods_per_year)

    result = values.rolling(
        window=window,
        min_periods=window,
    ).std(ddof=1) * math.sqrt(periods_per_year)

    result.name = "realized_volatility"

    return result


def classify_volatility_regime(
    volatility: float,
    *,
    low_threshold: float,
    high_threshold: float,
) -> VolatilityRegime:
    """Classify a volatility observation."""
    for name, value in {
        "volatility": volatility,
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
    }.items():
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(f"{name} must be numeric.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")

    volatility = float(volatility)

    low_threshold = float(low_threshold)

    high_threshold = float(high_threshold)

    if volatility < 0:
        raise ValueError("volatility cannot be negative.")

    if low_threshold < 0:
        raise ValueError("low_threshold cannot be negative.")

    if high_threshold <= low_threshold:
        raise ValueError("high_threshold must be greater than low_threshold.")

    if volatility < low_threshold:
        return VolatilityRegime.LOW

    if volatility > high_threshold:
        return VolatilityRegime.HIGH

    return VolatilityRegime.NORMAL


def _validate_quantiles(
    low_quantile: float,
    high_quantile: float,
) -> tuple[float, float]:
    for name, value in {
        "low_quantile": low_quantile,
        "high_quantile": high_quantile,
    }.items():
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(f"{name} must be numeric.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")

    low_quantile = float(low_quantile)

    high_quantile = float(high_quantile)

    if not 0 < low_quantile < 1:
        raise ValueError("low_quantile must be between 0 and 1.")

    if not 0 < high_quantile < 1:
        raise ValueError("high_quantile must be between 0 and 1.")

    if low_quantile >= high_quantile:
        raise ValueError("low_quantile must be smaller than high_quantile.")

    return (
        low_quantile,
        high_quantile,
    )


def rolling_volatility_regime(
    returns: pd.Series,
    *,
    window: int = 20,
    low_quantile: float = 0.25,
    high_quantile: float = 0.75,
    periods_per_year: int = 252,
) -> pd.Series:
    """Generate causal volatility regimes from historical quantiles."""
    volatility = rolling_realized_volatility(
        returns,
        window=window,
        periods_per_year=periods_per_year,
    )

    low_quantile, high_quantile = _validate_quantiles(
        low_quantile,
        high_quantile,
    )

    result = pd.Series(
        pd.NA,
        index=volatility.index,
        dtype="object",
        name="volatility_regime",
    )

    for index in range(
        window - 1,
        len(volatility),
    ):
        current = volatility.iloc[index]

        if pd.isna(current):
            continue

        historical = volatility.iloc[: index + 1].dropna()

        if len(historical) < 2:
            continue

        low_threshold = float(historical.quantile(low_quantile))

        high_threshold = float(historical.quantile(high_quantile))

        if math.isclose(
            low_threshold,
            high_threshold,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            result.iloc[index] = VolatilityRegime.NORMAL.value

            continue

        regime = classify_volatility_regime(
            float(current),
            low_threshold=low_threshold,
            high_threshold=high_threshold,
        )

        result.iloc[index] = regime.value

    return result
