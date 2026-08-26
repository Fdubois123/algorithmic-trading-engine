from __future__ import annotations

import math

import numpy as np
import pandas as pd

from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)


def construct_spread(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    hedge_ratio: float,
    intercept: float = 0.0,
) -> pd.Series:
    """Construct y - alpha - beta*x pair spread."""
    for name, value in {
        "hedge_ratio": hedge_ratio,
        "intercept": intercept,
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

    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
    )

    spread = (
        aligned["dependent"]
        - float(intercept)
        - float(hedge_ratio) * aligned["independent"]
    )

    spread.name = "spread"

    return spread


def rolling_spread_zscore(
    spread: pd.Series,
    *,
    window: int = 20,
    minimum_periods: int | None = None,
) -> pd.Series:
    """Calculate rolling z-score of a pair spread."""
    if not isinstance(
        spread,
        pd.Series,
    ):
        raise TypeError("spread must be a pandas Series.")

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

    if minimum_periods is None:
        minimum_periods = window

    if isinstance(
        minimum_periods,
        bool,
    ) or not isinstance(
        minimum_periods,
        int,
    ):
        raise TypeError("minimum_periods must be an integer.")

    if not 2 <= minimum_periods <= window:
        raise ValueError("minimum_periods must be between 2 and window.")

    if spread.empty:
        raise ValueError("spread cannot be empty.")

    try:
        values = spread.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("spread must contain numeric values.") from error

    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("spread must contain only finite values.")

    rolling_mean = values.rolling(
        window=window,
        min_periods=minimum_periods,
    ).mean()

    rolling_standard_deviation = values.rolling(
        window=window,
        min_periods=minimum_periods,
    ).std(ddof=1)

    denominator = rolling_standard_deviation.replace(
        0.0,
        np.nan,
    )

    result = (values - rolling_mean) / denominator

    result.name = "zscore"

    return result
