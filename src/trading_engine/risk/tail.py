from __future__ import annotations

import math

import numpy as np
import pandas as pd

from trading_engine.indicators._validation import validate_numeric_series


def _validate_confidence_level(confidence_level: float) -> None:
    if not isinstance(confidence_level, (int, float)) or isinstance(
        confidence_level,
        bool,
    ):
        raise TypeError("confidence_level must be numeric.")

    if not math.isfinite(float(confidence_level)):
        raise ValueError("confidence_level must be finite.")

    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be strictly between 0 and 1.")


def historical_var(
    returns: pd.Series,
    *,
    confidence_level: float = 0.95,
) -> float:
    """Calculate historical Value at Risk as a positive loss magnitude."""
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    _validate_confidence_level(confidence_level)

    clean = returns.dropna()

    if clean.empty:
        raise ValueError("Returns contain no valid observations.")

    quantile = np.quantile(
        clean.to_numpy(),
        1.0 - confidence_level,
    )

    return float(max(0.0, -quantile))


def historical_cvar(
    returns: pd.Series,
    *,
    confidence_level: float = 0.95,
) -> float:
    """Calculate historical CVaR / Expected Shortfall.

    Returns the positive magnitude of the average loss in the tail beyond VaR.
    """
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    _validate_confidence_level(confidence_level)

    clean = returns.dropna()

    if clean.empty:
        raise ValueError("Returns contain no valid observations.")

    cutoff = np.quantile(
        clean.to_numpy(),
        1.0 - confidence_level,
    )

    tail = clean[clean <= cutoff]

    if tail.empty:
        return 0.0

    return float(max(0.0, -tail.mean()))
