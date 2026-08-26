from __future__ import annotations

import math
from enum import Enum

import numpy as np
import pandas as pd


class DrawdownRegime(str, Enum):
    """Market drawdown state."""

    SHALLOW = "shallow"
    MODERATE = "moderate"
    DEEP = "deep"


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


def running_drawdown(
    prices: pd.Series,
) -> pd.Series:
    """Calculate current drawdown from the running price peak."""
    values = _validate_prices(prices)

    running_peak = values.cummax()

    drawdown = values / running_peak - 1.0

    drawdown.name = "drawdown"

    return drawdown


def classify_drawdown_regime(
    drawdown: float,
    *,
    moderate_threshold: float = -0.10,
    deep_threshold: float = -0.20,
) -> DrawdownRegime:
    """Classify a drawdown observation."""
    for name, value in {
        "drawdown": drawdown,
        "moderate_threshold": moderate_threshold,
        "deep_threshold": deep_threshold,
    }.items():
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(f"{name} must be numeric.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")

    drawdown = float(drawdown)
    moderate_threshold = float(moderate_threshold)
    deep_threshold = float(deep_threshold)

    if drawdown > 1e-12:
        raise ValueError("drawdown cannot be positive.")

    if moderate_threshold >= 0:
        raise ValueError("moderate_threshold must be negative.")

    if deep_threshold >= moderate_threshold:
        raise ValueError("deep_threshold must be smaller than moderate_threshold.")

    if drawdown <= deep_threshold:
        return DrawdownRegime.DEEP

    if drawdown <= moderate_threshold:
        return DrawdownRegime.MODERATE

    return DrawdownRegime.SHALLOW


def rolling_drawdown_regime(
    prices: pd.Series,
    *,
    moderate_threshold: float = -0.10,
    deep_threshold: float = -0.20,
) -> pd.Series:
    """Classify the current drawdown through time."""
    drawdown = running_drawdown(prices)

    result = pd.Series(
        pd.NA,
        index=drawdown.index,
        dtype="object",
        name="drawdown_regime",
    )

    for index, value in enumerate(drawdown):
        regime = classify_drawdown_regime(
            float(value),
            moderate_threshold=moderate_threshold,
            deep_threshold=deep_threshold,
        )

        result.iloc[index] = regime.value

    return result
