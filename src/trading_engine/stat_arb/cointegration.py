from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.stat_arb.hedge import (
    HedgeRatioResult,
    estimate_hedge_ratio,
)
from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)
from trading_engine.stat_arb.spread import (
    construct_spread,
)


@dataclass(slots=True, frozen=True)
class StationarityDiagnostic:
    """ADF-style residual stationarity diagnostic."""

    statistic: float
    critical_value: float
    stationary: bool
    lagged_coefficient: float
    observations: int


@dataclass(slots=True, frozen=True)
class EngleGrangerDiagnostic:
    """Dependency-light Engle-Granger style pair diagnostic."""

    hedge: HedgeRatioResult
    stationarity: StationarityDiagnostic

    @property
    def cointegrated(self) -> bool:
        return self.stationarity.stationary


def _validate_critical_value(
    critical_value: float,
) -> float:
    if isinstance(
        critical_value,
        bool,
    ) or not isinstance(
        critical_value,
        (int, float),
    ):
        raise TypeError("critical_value must be numeric.")

    critical_value = float(critical_value)

    if not math.isfinite(critical_value):
        raise ValueError("critical_value must be finite.")

    return critical_value


def residual_adf_statistic(
    residuals: pd.Series,
    *,
    critical_value: float = -3.34,
) -> StationarityDiagnostic:
    """Calculate a zero-lag ADF-style statistic for residual stationarity.

    Regression:

        Δe_t = c + gamma * e_(t-1) + error_t

    A sufficiently negative t-statistic for gamma indicates
    mean-reverting residuals.

    The default critical value is deliberately exposed as a parameter.
    It is an approximation rather than an exact MacKinnon p-value.
    """
    critical_value = _validate_critical_value(critical_value)

    if not isinstance(
        residuals,
        pd.Series,
    ):
        raise TypeError("residuals must be a pandas Series.")

    if residuals.empty:
        raise ValueError("residuals cannot be empty.")

    if len(residuals) < 5:
        raise ValueError("residuals must contain at least 5 observations.")

    try:
        values = residuals.astype(float).to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise TypeError("residuals must contain numeric values.") from error

    if not np.isfinite(values).all():
        raise ValueError("residuals must contain only finite values.")

    lagged = values[:-1]

    difference = np.diff(values)

    if np.var(lagged) <= 1e-15:
        raise ValueError("residuals must have non-zero lagged variance.")

    design = np.column_stack(
        [
            np.ones(
                len(lagged),
                dtype=float,
            ),
            lagged,
        ]
    )

    coefficients, *_ = np.linalg.lstsq(
        design,
        difference,
        rcond=None,
    )

    gamma = float(coefficients[1])

    fitted = design @ coefficients

    errors = difference - fitted

    degrees_of_freedom = len(difference) - design.shape[1]

    if degrees_of_freedom <= 0:
        raise ValueError("insufficient observations for stationarity regression.")

    residual_variance = float(errors @ errors / degrees_of_freedom)

    gram_inverse = np.linalg.pinv(
        design.T @ design,
        hermitian=True,
    )

    gamma_variance = float(residual_variance * gram_inverse[1, 1])

    if gamma_variance <= 1e-20:
        if gamma < 0:
            statistic = float("-inf")
        elif gamma > 0:
            statistic = float("inf")
        else:
            statistic = 0.0
    else:
        statistic = gamma / math.sqrt(gamma_variance)

    stationary = statistic < critical_value

    return StationarityDiagnostic(
        statistic=float(statistic),
        critical_value=critical_value,
        stationary=stationary,
        lagged_coefficient=gamma,
        observations=len(values),
    )


def engle_granger_diagnostic(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    critical_value: float = -3.34,
) -> EngleGrangerDiagnostic:
    """Run OLS hedge estimation followed by residual stationarity testing."""
    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=5,
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

    stationarity = residual_adf_statistic(
        spread,
        critical_value=critical_value,
    )

    return EngleGrangerDiagnostic(
        hedge=hedge,
        stationarity=stationarity,
    )
