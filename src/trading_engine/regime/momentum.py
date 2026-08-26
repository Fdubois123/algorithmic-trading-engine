from __future__ import annotations

import math
from enum import Enum

import numpy as np
import pandas as pd


class MomentumRegime(str, Enum):
    """Momentum state."""

    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


def _validate_prices(
    prices: pd.Series,
) -> pd.Series:
    if not isinstance(prices, pd.Series):
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


def rolling_momentum(
    prices: pd.Series,
    *,
    lookback: int = 20,
) -> pd.Series:
    """Calculate trailing percentage price momentum."""
    values = _validate_prices(prices)

    if isinstance(lookback, bool) or not isinstance(
        lookback,
        int,
    ):
        raise TypeError("lookback must be an integer.")

    if lookback <= 0:
        raise ValueError("lookback must be greater than zero.")

    result = values / values.shift(lookback) - 1.0

    result.name = "momentum"

    return result


def classify_momentum_regime(
    momentum: float,
    *,
    threshold: float = 0.02,
) -> MomentumRegime:
    """Classify one momentum observation."""
    for name, value in {
        "momentum": momentum,
        "threshold": threshold,
    }.items():
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(f"{name} must be numeric.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")

    momentum = float(momentum)
    threshold = float(threshold)

    if threshold < 0:
        raise ValueError("threshold cannot be negative.")

    if momentum > threshold:
        return MomentumRegime.POSITIVE

    if momentum < -threshold:
        return MomentumRegime.NEGATIVE

    return MomentumRegime.NEUTRAL


def rolling_momentum_regime(
    prices: pd.Series,
    *,
    lookback: int = 20,
    threshold: float = 0.02,
) -> pd.Series:
    """Generate trailing momentum regimes."""
    momentum = rolling_momentum(
        prices,
        lookback=lookback,
    )

    result = pd.Series(
        pd.NA,
        index=momentum.index,
        dtype="object",
        name="momentum_regime",
    )

    for index, value in enumerate(momentum):
        if pd.isna(value):
            continue

        regime = classify_momentum_regime(
            float(value),
            threshold=threshold,
        )

        result.iloc[index] = regime.value

    return result
