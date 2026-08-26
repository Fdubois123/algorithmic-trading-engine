from __future__ import annotations

import math

import numpy as np

from trading_engine.portfolio.optimization import (
    equal_weight_portfolio,
)
from trading_engine.portfolio.validation import (
    validate_covariance_matrix,
    validate_weights,
)


def marginal_risk_contributions(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> np.ndarray:
    """Return each asset's marginal contribution to volatility."""
    matrix = validate_covariance_matrix(covariance)

    allocation = validate_weights(
        weights,
        number_of_assets=matrix.shape[0],
        allow_short=True,
    )

    variance = float(allocation @ matrix @ allocation)

    if variance <= 0:
        return np.zeros(
            matrix.shape[0],
            dtype=float,
        )

    volatility = math.sqrt(variance)

    return (matrix @ allocation) / volatility


def risk_contributions(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> np.ndarray:
    """Return additive asset contributions to portfolio volatility."""
    allocation = validate_weights(
        weights,
        allow_short=True,
    )

    marginal = marginal_risk_contributions(
        allocation,
        covariance,
    )

    return allocation * marginal


def percentage_risk_contributions(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> np.ndarray:
    """Return each asset's fraction of total portfolio risk."""
    contributions = risk_contributions(
        weights,
        covariance,
    )

    total = float(contributions.sum())

    if abs(total) <= 1e-15:
        return np.zeros_like(contributions)

    return contributions / total


def risk_parity_weights(
    covariance: np.ndarray,
    *,
    tolerance: float = 1e-8,
    max_iterations: int = 10_000,
) -> np.ndarray:
    """Estimate a long-only equal-risk-contribution portfolio.

    Uses multiplicative updates and normalization. The method is
    dependency-light and deterministic, making it suitable for the
    engine's core implementation.
    """
    matrix = validate_covariance_matrix(covariance)

    if isinstance(
        tolerance,
        bool,
    ) or not isinstance(
        tolerance,
        (int, float),
    ):
        raise TypeError("tolerance must be numeric.")

    tolerance = float(tolerance)

    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and greater than zero.")

    if isinstance(
        max_iterations,
        bool,
    ) or not isinstance(
        max_iterations,
        int,
    ):
        raise TypeError("max_iterations must be an integer.")

    if max_iterations <= 0:
        raise ValueError("max_iterations must be greater than zero.")

    asset_count = matrix.shape[0]

    if asset_count == 1:
        return np.array(
            [1.0],
            dtype=float,
        )

    diagonal = np.diag(matrix)

    if np.all(diagonal <= 1e-15):
        return equal_weight_portfolio(asset_count)

    weights = equal_weight_portfolio(asset_count)

    target = 1.0 / asset_count

    epsilon = 1e-15

    for _ in range(max_iterations):
        contributions = percentage_risk_contributions(
            weights,
            matrix,
        )

        if np.any(contributions < 0):
            raise ValueError("risk parity requires non-negative risk contributions.")

        error = float(np.max(np.abs(contributions - target)))

        if error <= tolerance:
            return weights

        safe_contributions = np.maximum(
            contributions,
            epsilon,
        )

        weights *= (target / safe_contributions) ** 0.5

        weights = np.maximum(
            weights,
            epsilon,
        )

        weights /= weights.sum()

    raise RuntimeError("risk parity failed to converge.")
