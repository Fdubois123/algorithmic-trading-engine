from __future__ import annotations

import math

import numpy as np
import pandas as pd

from trading_engine.portfolio.validation import (
    validate_covariance_matrix,
)


def _validate_returns(
    returns: pd.DataFrame,
) -> pd.DataFrame:
    if not isinstance(
        returns,
        pd.DataFrame,
    ):
        raise TypeError("returns must be a pandas DataFrame.")

    if returns.empty:
        raise ValueError("returns cannot be empty.")

    if returns.shape[1] == 0:
        raise ValueError("returns must contain at least one asset.")

    if returns.shape[0] < 2:
        raise ValueError("returns must contain at least two observations.")

    try:
        numeric = returns.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("returns must contain numeric values.") from error

    values = numeric.to_numpy()

    if not np.isfinite(values).all():
        raise ValueError("returns must contain only finite values.")

    return numeric


def sample_expected_returns(
    returns: pd.DataFrame,
    *,
    periods_per_year: int = 252,
) -> pd.Series:
    """Estimate annualized arithmetic expected returns."""
    frame = _validate_returns(returns)

    if isinstance(
        periods_per_year,
        bool,
    ) or not isinstance(
        periods_per_year,
        int,
    ):
        raise TypeError("periods_per_year must be an integer.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")

    result = frame.mean() * periods_per_year

    result.name = "expected_return"

    return result


def sample_covariance(
    returns: pd.DataFrame,
    *,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Estimate annualized sample covariance."""
    frame = _validate_returns(returns)

    if isinstance(
        periods_per_year,
        bool,
    ) or not isinstance(
        periods_per_year,
        int,
    ):
        raise TypeError("periods_per_year must be an integer.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")

    covariance = frame.cov() * periods_per_year

    validate_covariance_matrix(covariance.to_numpy())

    return covariance


def exponentially_weighted_covariance(
    returns: pd.DataFrame,
    *,
    decay: float = 0.94,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Estimate covariance using exponentially decaying observations."""
    frame = _validate_returns(returns)

    if isinstance(
        decay,
        bool,
    ) or not isinstance(
        decay,
        (int, float),
    ):
        raise TypeError("decay must be numeric.")

    decay = float(decay)

    if not math.isfinite(decay):
        raise ValueError("decay must be finite.")

    if not 0 < decay < 1:
        raise ValueError("decay must be between 0 and 1.")

    if isinstance(
        periods_per_year,
        bool,
    ) or not isinstance(
        periods_per_year,
        int,
    ):
        raise TypeError("periods_per_year must be an integer.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")

    values = frame.to_numpy(dtype=float)

    observation_count = len(frame)

    powers = np.arange(
        observation_count - 1,
        -1,
        -1,
        dtype=float,
    )

    weights = np.power(
        decay,
        powers,
    )

    weights /= weights.sum()

    mean = np.sum(
        values * weights[:, None],
        axis=0,
    )

    centered = values - mean

    denominator = 1.0 - float(np.sum(weights**2))

    if denominator <= 0:
        raise ValueError(
            "insufficient effective observations for covariance estimation."
        )

    covariance = ((centered * weights[:, None]).T @ centered) / denominator

    covariance *= periods_per_year

    validate_covariance_matrix(covariance)

    return pd.DataFrame(
        covariance,
        index=frame.columns,
        columns=frame.columns,
    )
