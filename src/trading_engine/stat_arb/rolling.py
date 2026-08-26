from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.stat_arb.hedge import (
    estimate_hedge_ratio,
)
from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)


@dataclass(slots=True, frozen=True)
class RollingHedgeResult:
    """Rolling or expanding hedge-ratio estimates."""

    alpha: pd.Series
    beta: pd.Series
    r_squared: pd.Series
    residual_variance: pd.Series

    @property
    def index(self) -> pd.Index:
        return self.beta.index

    @property
    def observations(self) -> int:
        return len(self.beta)


def _validate_window(
    window: int,
    *,
    minimum: int = 3,
) -> int:
    if isinstance(window, bool) or not isinstance(
        window,
        int,
    ):
        raise TypeError("window must be an integer.")

    if window < minimum:
        raise ValueError(f"window must be at least {minimum}.")

    return window


def rolling_hedge_ratio(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    window: int = 60,
    include_intercept: bool = True,
) -> RollingHedgeResult:
    """Estimate hedge parameters using trailing windows only."""
    window = _validate_window(window)

    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=window,
    )

    alpha = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    beta = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    r_squared = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    residual_variance = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    for end in range(
        window - 1,
        len(aligned),
    ):
        start = end - window + 1

        sample = aligned.iloc[start : end + 1]

        result = estimate_hedge_ratio(
            sample["dependent"],
            sample["independent"],
            include_intercept=include_intercept,
        )

        alpha[end] = result.alpha
        beta[end] = result.beta
        r_squared[end] = result.r_squared
        residual_variance[end] = result.residual_variance

    index = aligned.index

    return RollingHedgeResult(
        alpha=pd.Series(
            alpha,
            index=index,
            name="rolling_alpha",
        ),
        beta=pd.Series(
            beta,
            index=index,
            name="rolling_beta",
        ),
        r_squared=pd.Series(
            r_squared,
            index=index,
            name="rolling_r_squared",
        ),
        residual_variance=pd.Series(
            residual_variance,
            index=index,
            name="rolling_residual_variance",
        ),
    )


def expanding_hedge_ratio(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    minimum_observations: int = 20,
    include_intercept: bool = True,
) -> RollingHedgeResult:
    """Estimate hedge parameters using expanding historical samples."""
    minimum_observations = _validate_window(minimum_observations)

    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=minimum_observations,
    )

    alpha = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    beta = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    r_squared = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    residual_variance = np.full(
        len(aligned),
        np.nan,
        dtype=float,
    )

    for end in range(
        minimum_observations - 1,
        len(aligned),
    ):
        sample = aligned.iloc[: end + 1]

        result = estimate_hedge_ratio(
            sample["dependent"],
            sample["independent"],
            include_intercept=include_intercept,
        )

        alpha[end] = result.alpha
        beta[end] = result.beta
        r_squared[end] = result.r_squared
        residual_variance[end] = result.residual_variance

    index = aligned.index

    return RollingHedgeResult(
        alpha=pd.Series(
            alpha,
            index=index,
            name="expanding_alpha",
        ),
        beta=pd.Series(
            beta,
            index=index,
            name="expanding_beta",
        ),
        r_squared=pd.Series(
            r_squared,
            index=index,
            name="expanding_r_squared",
        ),
        residual_variance=pd.Series(
            residual_variance,
            index=index,
            name="expanding_residual_variance",
        ),
    )


def walk_forward_spread(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    hedge: RollingHedgeResult,
) -> pd.Series:
    """Construct a spread using contemporaneously available hedge estimates."""
    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
    )

    alpha = hedge.alpha.reindex(aligned.index)

    beta = hedge.beta.reindex(aligned.index)

    spread = aligned["dependent"] - alpha - beta * aligned["independent"]

    spread.name = "walk_forward_spread"

    return spread
