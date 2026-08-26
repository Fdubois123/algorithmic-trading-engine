from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)


@dataclass(slots=True, frozen=True)
class HedgeRatioResult:
    """OLS hedge-ratio estimation result."""

    alpha: float
    beta: float
    residual_variance: float
    r_squared: float
    observations: int


def estimate_hedge_ratio(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    include_intercept: bool = True,
) -> HedgeRatioResult:
    """Estimate y = alpha + beta*x using ordinary least squares."""
    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=3,
    )

    y = aligned["dependent"].to_numpy(dtype=float)

    x = aligned["independent"].to_numpy(dtype=float)

    if np.var(x) <= 1e-15:
        raise ValueError("independent price series must have non-zero variance.")

    if include_intercept:
        design = np.column_stack(
            [
                np.ones(
                    len(x),
                    dtype=float,
                ),
                x,
            ]
        )

        coefficients, *_ = np.linalg.lstsq(
            design,
            y,
            rcond=None,
        )

        alpha = float(coefficients[0])

        beta = float(coefficients[1])

        fitted = alpha + beta * x
    else:
        denominator = float(x @ x)

        if denominator <= 1e-15:
            raise ValueError("independent price series has insufficient magnitude.")

        alpha = 0.0

        beta = float((x @ y) / denominator)

        fitted = beta * x

    residuals = y - fitted

    residual_sum_squares = float(residuals @ residuals)

    centered = y - y.mean()

    total_sum_squares = float(centered @ centered)

    if total_sum_squares <= 1e-15:
        r_squared = 1.0 if residual_sum_squares <= 1e-15 else 0.0
    else:
        r_squared = 1.0 - residual_sum_squares / total_sum_squares

    degrees_of_freedom = len(y) - (2 if include_intercept else 1)

    if degrees_of_freedom <= 0:
        raise ValueError("insufficient observations for hedge-ratio estimation.")

    residual_variance = residual_sum_squares / degrees_of_freedom

    return HedgeRatioResult(
        alpha=alpha,
        beta=beta,
        residual_variance=float(residual_variance),
        r_squared=float(r_squared),
        observations=len(y),
    )
