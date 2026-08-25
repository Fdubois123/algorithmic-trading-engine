from __future__ import annotations

import numpy as np
import pandas as pd

from trading_engine.indicators._validation import validate_positive_series


def drawdown_series(wealth: pd.Series) -> pd.Series:
    """Calculate percentage drawdown from the running wealth peak.

    Drawdown_t = Wealth_t / RunningPeak_t - 1

    Returns:
        Series bounded above by zero. Zero indicates a new/high-water mark.
    """
    validate_positive_series(wealth, name="Wealth")

    running_peak = wealth.cummax()
    result = wealth / running_peak - 1.0
    result.name = "drawdown"

    return result


def max_drawdown(wealth: pd.Series) -> float:
    """Calculate maximum observed drawdown."""
    result = drawdown_series(wealth)

    return float(result.min())


def underwater_curve(wealth: pd.Series) -> pd.Series:
    """Return drawdown depth as a positive percentage below the peak."""
    result = -drawdown_series(wealth)
    result.name = "underwater"

    return result


def drawdown_duration(wealth: pd.Series) -> pd.Series:
    """Calculate consecutive periods spent below the running wealth peak."""
    drawdown = drawdown_series(wealth)

    durations = np.zeros(len(drawdown), dtype=int)
    current = 0

    for index, value in enumerate(drawdown):
        if value < 0:
            current += 1
        else:
            current = 0

        durations[index] = current

    return pd.Series(
        durations,
        index=wealth.index,
        name="drawdown_duration",
    )
