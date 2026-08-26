from __future__ import annotations

import math

import numpy as np
import pandas as pd

from trading_engine.regime.labels import (
    TrendRegime,
)


def _validate_prices(
    prices: pd.Series,
) -> pd.Series:
    if not isinstance(
        prices,
        pd.Series,
    ):
        raise TypeError("prices must be a pandas Series.")

    if prices.empty:
        raise ValueError("prices cannot be empty.")

    try:
        values = prices.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("prices must contain numeric values.") from error

    array = values.to_numpy(dtype=float)

    if not np.isfinite(array).all():
        raise ValueError("prices must contain only finite values.")

    if np.any(array <= 0):
        raise ValueError("prices must be strictly positive.")

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


def rolling_trend_strength(
    prices: pd.Series,
    *,
    window: int = 50,
) -> pd.Series:
    """Calculate trailing normalized linear trend strength."""
    values = _validate_prices(prices)

    window = _validate_window(window)

    result = pd.Series(
        np.nan,
        index=values.index,
        dtype=float,
        name="trend_strength",
    )

    x = np.arange(
        window,
        dtype=float,
    )

    x_centered = x - x.mean()

    denominator = float(x_centered @ x_centered)

    for index in range(
        window - 1,
        len(values),
    ):
        sample = values.iloc[index - window + 1 : index + 1].to_numpy(dtype=float)

        sample_mean = float(sample.mean())

        if sample_mean <= 0:
            continue

        slope = float(x_centered @ (sample - sample.mean()) / denominator)

        result.iloc[index] = slope / sample_mean

    return result


def classify_trend_regime(
    trend_strength: float,
    *,
    threshold: float = 0.001,
) -> TrendRegime:
    """Classify normalized trend strength."""
    for name, value in {
        "trend_strength": trend_strength,
        "threshold": threshold,
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

    trend_strength = float(trend_strength)

    threshold = float(threshold)

    if threshold < 0:
        raise ValueError("threshold cannot be negative.")

    if trend_strength > threshold:
        return TrendRegime.BULL

    if trend_strength < -threshold:
        return TrendRegime.BEAR

    return TrendRegime.SIDEWAYS


def rolling_trend_regime(
    prices: pd.Series,
    *,
    window: int = 50,
    threshold: float = 0.001,
) -> pd.Series:
    """Generate trailing trend regimes."""
    strength = rolling_trend_strength(
        prices,
        window=window,
    )

    result = pd.Series(
        pd.NA,
        index=strength.index,
        dtype="object",
        name="trend_regime",
    )

    for index, value in enumerate(strength):
        if pd.isna(value):
            continue

        regime = classify_trend_regime(
            float(value),
            threshold=threshold,
        )

        result.iloc[index] = regime.value

    return result
