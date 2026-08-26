from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.stat_arb.hedge import (
    HedgeRatioResult,
    estimate_hedge_ratio,
)
from trading_engine.stat_arb.mean_reversion import (
    MeanReversionResult,
    estimate_mean_reversion,
)
from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)
from trading_engine.stat_arb.spread import (
    construct_spread,
)


@dataclass(slots=True, frozen=True)
class PairDiagnostics:
    """Summary diagnostics for a statistical-arbitrage pair."""

    hedge: HedgeRatioResult
    mean_reversion: MeanReversionResult
    price_correlation: float
    spread_mean: float
    spread_standard_deviation: float
    observations: int


def pair_price_correlation(
    first: pd.Series,
    second: pd.Series,
) -> float:
    """Calculate aligned price-level correlation."""
    aligned = align_pair_prices(
        first,
        second,
        first_name="first",
        second_name="second",
        minimum_observations=2,
    )

    first_values = aligned["first"].to_numpy(dtype=float)

    second_values = aligned["second"].to_numpy(dtype=float)

    if np.var(first_values) <= 1e-15 or np.var(second_values) <= 1e-15:
        raise ValueError("both price series must have non-zero variance.")

    correlation = float(
        np.corrcoef(
            first_values,
            second_values,
        )[0, 1]
    )

    if not np.isfinite(correlation):
        raise ValueError("pair correlation must be finite.")

    return correlation


def diagnose_pair(
    dependent: pd.Series,
    independent: pd.Series,
) -> PairDiagnostics:
    """Run dependency-light statistical-arbitrage diagnostics."""
    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=3,
    )

    hedge = estimate_hedge_ratio(
        aligned["dependent"],
        aligned["independent"],
    )

    spread = construct_spread(
        aligned["dependent"],
        aligned["independent"],
        hedge_ratio=hedge.beta,
        intercept=hedge.alpha,
    )

    mean_reversion = estimate_mean_reversion(spread)

    correlation = pair_price_correlation(
        aligned["dependent"],
        aligned["independent"],
    )

    return PairDiagnostics(
        hedge=hedge,
        mean_reversion=mean_reversion,
        price_correlation=correlation,
        spread_mean=float(spread.mean()),
        spread_standard_deviation=float(spread.std(ddof=1)),
        observations=len(aligned),
    )
