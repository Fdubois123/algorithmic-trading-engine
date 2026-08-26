from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.research.attribution import (
    contribution_totals,
)
from trading_engine.research.regime_analysis import (
    regime_performance,
)


@dataclass(slots=True, frozen=True)
class StrategyRanking:
    """Ranked strategy contribution."""

    rank: int
    strategy: str
    contribution: float


@dataclass(slots=True, frozen=True)
class RegimeRanking:
    """Ranked market-regime performance."""

    rank: int
    regime: str
    cumulative_return: float
    average_return: float
    observations: int


def rank_strategies(
    strategy_returns: pd.DataFrame,
    applied_weights: pd.DataFrame,
) -> tuple[
    StrategyRanking,
    ...,
]:
    """Rank strategies by cumulative contribution."""
    totals = contribution_totals(
        strategy_returns,
        applied_weights,
    )

    ordered = totals.sort_values(ascending=False)

    return tuple(
        StrategyRanking(
            rank=rank,
            strategy=strategy,
            contribution=float(value),
        )
        for rank, (
            strategy,
            value,
        ) in enumerate(
            ordered.items(),
            start=1,
        )
    )


def rank_regimes(
    returns: pd.Series,
    regimes: pd.Series,
) -> tuple[
    RegimeRanking,
    ...,
]:
    """Rank regimes by compounded return."""
    performance = regime_performance(
        returns,
        regimes,
    )

    ordered = sorted(
        performance,
        key=lambda item: item.cumulative_return,
        reverse=True,
    )

    return tuple(
        RegimeRanking(
            rank=rank,
            regime=item.regime,
            cumulative_return=float(item.cumulative_return),
            average_return=float(item.average_return),
            observations=int(item.observations),
        )
        for rank, item in enumerate(
            ordered,
            start=1,
        )
    )


def strategy_ranking_table(
    strategy_returns: pd.DataFrame,
    applied_weights: pd.DataFrame,
) -> pd.DataFrame:
    """Return ranked strategies as a DataFrame."""
    rankings = rank_strategies(
        strategy_returns,
        applied_weights,
    )

    return pd.DataFrame(
        [
            {
                "rank": item.rank,
                "strategy": item.strategy,
                "contribution": item.contribution,
            }
            for item in rankings
        ]
    )


def regime_ranking_table(
    returns: pd.Series,
    regimes: pd.Series,
) -> pd.DataFrame:
    """Return ranked regimes as a DataFrame."""
    rankings = rank_regimes(
        returns,
        regimes,
    )

    frame = pd.DataFrame(
        [
            {
                "rank": item.rank,
                "regime": item.regime,
                "cumulative_return": (item.cumulative_return),
                "average_return": (item.average_return),
                "observations": (item.observations),
            }
            for item in rankings
        ]
    )

    if not frame.empty:
        numeric = frame[
            [
                "cumulative_return",
                "average_return",
            ]
        ].to_numpy(dtype=float)

        if not np.isfinite(numeric).all():
            raise ValueError("regime ranking contains non-finite values.")

    return frame
