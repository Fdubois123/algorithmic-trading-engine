from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True, frozen=True)
class RegimePerformance:
    """Portfolio performance within one market regime."""

    regime: str
    observations: int
    average_return: float
    cumulative_return: float
    volatility: float
    win_rate: float


def _validate_regime_inputs(
    returns: pd.Series,
    regimes: pd.Series,
) -> tuple[
    pd.Series,
    pd.Series,
]:
    if not isinstance(
        returns,
        pd.Series,
    ):
        raise TypeError("returns must be a pandas Series.")

    if not isinstance(
        regimes,
        pd.Series,
    ):
        raise TypeError("regimes must be a pandas Series.")

    if returns.empty:
        raise ValueError("returns cannot be empty.")

    if not returns.index.equals(regimes.index):
        raise ValueError("returns and regimes must have matching indexes.")

    try:
        return_values = returns.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError("returns must contain numeric values.") from error

    if not np.isfinite(return_values.to_numpy(dtype=float)).all():
        raise ValueError("returns must contain only finite values.")

    return (
        return_values,
        regimes.copy(),
    )


def regime_performance(
    returns: pd.Series,
    regimes: pd.Series,
) -> tuple[
    RegimePerformance,
    ...,
]:
    """Summarize portfolio performance by market regime."""
    return_values, regime_values = _validate_regime_inputs(
        returns,
        regimes,
    )

    frame = pd.DataFrame(
        {
            "return": return_values,
            "regime": regime_values,
        }
    )

    frame = frame.dropna(
        subset=[
            "regime",
        ]
    )

    results: list[RegimePerformance] = []

    for regime, group in frame.groupby(
        "regime",
        sort=True,
    ):
        values = group["return"]

        cumulative = float((1.0 + values).prod() - 1.0)

        if len(values) < 2:
            volatility = 0.0
        else:
            volatility = float(values.std(ddof=1))

        win_rate = float((values > 0).mean())

        results.append(
            RegimePerformance(
                regime=str(regime),
                observations=len(values),
                average_return=float(values.mean()),
                cumulative_return=cumulative,
                volatility=volatility,
                win_rate=win_rate,
            )
        )

    return tuple(results)


def regime_return_table(
    returns: pd.Series,
    regimes: pd.Series,
) -> pd.DataFrame:
    """Return regime performance as a DataFrame."""
    records = regime_performance(
        returns,
        regimes,
    )

    return pd.DataFrame(
        [
            {
                "regime": item.regime,
                "observations": item.observations,
                "average_return": item.average_return,
                "cumulative_return": item.cumulative_return,
                "volatility": item.volatility,
                "win_rate": item.win_rate,
            }
            for item in records
        ]
    )
