from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True, frozen=True)
class StrategyAttribution:
    """Contribution statistics for one strategy."""

    strategy: str
    cumulative_contribution: float
    average_contribution: float
    positive_periods: int
    negative_periods: int


def strategy_contribution_frame(
    strategy_returns: pd.DataFrame,
    applied_weights: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate per-period strategy return contributions."""
    if not isinstance(
        strategy_returns,
        pd.DataFrame,
    ):
        raise TypeError("strategy_returns must be a pandas DataFrame.")

    if not isinstance(
        applied_weights,
        pd.DataFrame,
    ):
        raise TypeError("applied_weights must be a pandas DataFrame.")

    if strategy_returns.empty:
        raise ValueError("strategy_returns cannot be empty.")

    if not strategy_returns.index.equals(applied_weights.index):
        raise ValueError(
            "strategy_returns and applied_weights must have matching indexes."
        )

    if list(strategy_returns.columns) != list(applied_weights.columns):
        raise ValueError(
            "strategy_returns and applied_weights must have matching columns."
        )

    try:
        returns = strategy_returns.astype(float)

        weights = applied_weights.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("strategy returns and weights must be numeric.") from error

    if not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("strategy_returns must contain only finite values.")

    if not np.isfinite(weights.to_numpy(dtype=float)).all():
        raise ValueError("applied_weights must contain only finite values.")

    contribution = returns * weights

    contribution.columns.name = "strategy"

    return contribution


def strategy_attribution(
    strategy_returns: pd.DataFrame,
    applied_weights: pd.DataFrame,
) -> tuple[
    StrategyAttribution,
    ...,
]:
    """Summarize contribution of each strategy."""
    contribution = strategy_contribution_frame(
        strategy_returns,
        applied_weights,
    )

    results: list[StrategyAttribution] = []

    for strategy in contribution.columns:
        values = contribution[strategy]

        results.append(
            StrategyAttribution(
                strategy=strategy,
                cumulative_contribution=float(values.sum()),
                average_contribution=float(values.mean()),
                positive_periods=int((values > 0).sum()),
                negative_periods=int((values < 0).sum()),
            )
        )

    return tuple(results)


def contribution_totals(
    strategy_returns: pd.DataFrame,
    applied_weights: pd.DataFrame,
) -> pd.Series:
    """Return total contribution by strategy."""
    contribution = strategy_contribution_frame(
        strategy_returns,
        applied_weights,
    )

    result = contribution.sum(axis=0).astype(float)

    result.name = "cumulative_contribution"

    return result
