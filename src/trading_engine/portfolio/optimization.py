from __future__ import annotations

import math

import numpy as np

from trading_engine.portfolio.validation import (
    validate_covariance_matrix,
    validate_expected_returns,
    validate_weights,
)


def equal_weight_portfolio(
    number_of_assets: int,
) -> np.ndarray:
    """Return a fully invested equal-weight portfolio."""
    if isinstance(
        number_of_assets,
        bool,
    ) or not isinstance(
        number_of_assets,
        int,
    ):
        raise TypeError("number_of_assets must be an integer.")

    if number_of_assets <= 0:
        raise ValueError("number_of_assets must be greater than zero.")

    return np.full(
        number_of_assets,
        1.0 / number_of_assets,
        dtype=float,
    )


def portfolio_return(
    weights: np.ndarray,
    expected_returns: np.ndarray,
) -> float:
    """Calculate expected portfolio return."""
    expected = validate_expected_returns(expected_returns)

    allocation = validate_weights(
        weights,
        number_of_assets=expected.size,
        allow_short=True,
    )

    return float(allocation @ expected)


def portfolio_variance(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Calculate portfolio variance."""
    matrix = validate_covariance_matrix(covariance)

    allocation = validate_weights(
        weights,
        number_of_assets=matrix.shape[0],
        allow_short=True,
    )

    variance = float(allocation @ matrix @ allocation)

    return max(
        variance,
        0.0,
    )


def portfolio_volatility(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Calculate portfolio volatility."""
    return math.sqrt(
        portfolio_variance(
            weights,
            covariance,
        )
    )


def minimum_variance_weights(
    covariance: np.ndarray,
    *,
    allow_short: bool = False,
) -> np.ndarray:
    """Calculate minimum-variance portfolio weights.

    The unconstrained solution uses the covariance pseudo-inverse.

    When short selling is disabled, negative unconstrained weights
    are projected to zero and the remaining allocation is normalized.
    """
    matrix = validate_covariance_matrix(covariance)

    asset_count = matrix.shape[0]

    ones = np.ones(
        asset_count,
        dtype=float,
    )

    inverse = np.linalg.pinv(
        matrix,
        hermitian=True,
    )

    raw_weights = inverse @ ones

    denominator = float(ones @ raw_weights)

    if abs(denominator) <= 1e-15:
        raise ValueError("minimum-variance portfolio cannot be determined.")

    weights = raw_weights / denominator

    if not allow_short:
        weights = np.maximum(
            weights,
            0.0,
        )

        total = float(weights.sum())

        if total <= 1e-15:
            return equal_weight_portfolio(asset_count)

        weights /= total

    validate_weights(
        weights,
        number_of_assets=asset_count,
        allow_short=allow_short,
    )

    return weights


def maximum_sharpe_weights(
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    *,
    risk_free_rate: float = 0.0,
    allow_short: bool = False,
) -> np.ndarray:
    """Calculate tangency-portfolio weights."""
    matrix = validate_covariance_matrix(covariance)

    expected = validate_expected_returns(
        expected_returns,
        number_of_assets=matrix.shape[0],
    )

    if isinstance(
        risk_free_rate,
        bool,
    ) or not isinstance(
        risk_free_rate,
        (int, float),
    ):
        raise TypeError("risk_free_rate must be numeric.")

    risk_free_rate = float(risk_free_rate)

    if not math.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite.")

    excess_returns = expected - risk_free_rate

    inverse = np.linalg.pinv(
        matrix,
        hermitian=True,
    )

    raw_weights = inverse @ excess_returns

    if not allow_short:
        raw_weights = np.maximum(
            raw_weights,
            0.0,
        )

    denominator = float(raw_weights.sum())

    if abs(denominator) <= 1e-15:
        raise ValueError(
            "maximum-Sharpe portfolio cannot be determined from the supplied inputs."
        )

    weights = raw_weights / denominator

    validate_weights(
        weights,
        number_of_assets=matrix.shape[0],
        allow_short=allow_short,
    )

    return weights
