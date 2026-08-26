from __future__ import annotations

import math

import numpy as np

from trading_engine.portfolio.optimization import (
    maximum_sharpe_weights,
)
from trading_engine.portfolio.validation import (
    validate_covariance_matrix,
    validate_expected_returns,
    validate_weights,
)


def _validate_positive_scalar(
    value: float,
    *,
    name: str,
) -> float:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def market_implied_returns(
    covariance: np.ndarray,
    market_weights: np.ndarray,
    *,
    risk_aversion: float = 2.5,
) -> np.ndarray:
    """Calculate Black–Litterman equilibrium excess returns."""
    matrix = validate_covariance_matrix(covariance)

    weights = validate_weights(
        market_weights,
        number_of_assets=matrix.shape[0],
        allow_short=False,
    )

    risk_aversion = _validate_positive_scalar(
        risk_aversion,
        name="risk_aversion",
    )

    return risk_aversion * matrix @ weights


def validate_views(
    pick_matrix: np.ndarray,
    view_returns: np.ndarray,
    *,
    number_of_assets: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate Black–Litterman investor views."""
    matrix = np.asarray(
        pick_matrix,
        dtype=float,
    )

    views = np.asarray(
        view_returns,
        dtype=float,
    )

    if matrix.ndim != 2:
        raise ValueError("pick_matrix must be two-dimensional.")

    if matrix.shape[0] == 0:
        raise ValueError("pick_matrix cannot be empty.")

    if matrix.shape[1] != number_of_assets:
        raise ValueError("pick_matrix columns must match the number of assets.")

    if not np.isfinite(matrix).all():
        raise ValueError("pick_matrix must contain only finite values.")

    if np.any(
        np.all(
            np.isclose(
                matrix,
                0.0,
            ),
            axis=1,
        )
    ):
        raise ValueError("each Black-Litterman view must reference at least one asset.")

    views = validate_expected_returns(views)

    if views.size != matrix.shape[0]:
        raise ValueError("view_returns length must match the number of views.")

    return matrix, views


def default_view_uncertainty(
    covariance: np.ndarray,
    pick_matrix: np.ndarray,
    *,
    tau: float = 0.05,
) -> np.ndarray:
    """Construct diagonal Black–Litterman view uncertainty."""
    matrix = validate_covariance_matrix(covariance)

    tau = _validate_positive_scalar(
        tau,
        name="tau",
    )

    picks, _ = validate_views(
        pick_matrix,
        np.zeros(np.asarray(pick_matrix).shape[0]),
        number_of_assets=matrix.shape[0],
    )

    scaled_covariance = tau * matrix

    projected = picks @ scaled_covariance @ picks.T

    diagonal = np.diag(projected)

    if np.any(diagonal <= 0):
        raise ValueError("view uncertainty must be strictly positive.")

    return np.diag(diagonal)


def black_litterman_posterior(
    covariance: np.ndarray,
    market_weights: np.ndarray,
    pick_matrix: np.ndarray,
    view_returns: np.ndarray,
    *,
    risk_aversion: float = 2.5,
    tau: float = 0.05,
    omega: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate Black–Litterman posterior returns and covariance."""
    matrix = validate_covariance_matrix(covariance)

    weights = validate_weights(
        market_weights,
        number_of_assets=matrix.shape[0],
        allow_short=False,
    )

    tau = _validate_positive_scalar(
        tau,
        name="tau",
    )

    picks, views = validate_views(
        pick_matrix,
        view_returns,
        number_of_assets=matrix.shape[0],
    )

    equilibrium = market_implied_returns(
        matrix,
        weights,
        risk_aversion=risk_aversion,
    )

    if omega is None:
        uncertainty = default_view_uncertainty(
            matrix,
            picks,
            tau=tau,
        )
    else:
        uncertainty = validate_covariance_matrix(omega)

        if uncertainty.shape != (
            picks.shape[0],
            picks.shape[0],
        ):
            raise ValueError("omega dimensions must match the number of views.")

        if np.any(np.diag(uncertainty) <= 0):
            raise ValueError("omega diagonal must be strictly positive.")

    prior_covariance = tau * matrix

    view_covariance = picks @ prior_covariance @ picks.T + uncertainty

    view_inverse = np.linalg.pinv(
        view_covariance,
        hermitian=True,
    )

    adjustment = (
        prior_covariance @ picks.T @ view_inverse @ (views - picks @ equilibrium)
    )

    posterior_returns = equilibrium + adjustment

    posterior_mean_covariance = (
        prior_covariance
        - prior_covariance @ picks.T @ view_inverse @ picks @ prior_covariance
    )

    posterior_covariance = matrix + posterior_mean_covariance

    posterior_covariance = (posterior_covariance + posterior_covariance.T) / 2.0

    validate_covariance_matrix(posterior_covariance)

    return (
        posterior_returns,
        posterior_covariance,
    )


def black_litterman_weights(
    covariance: np.ndarray,
    market_weights: np.ndarray,
    pick_matrix: np.ndarray,
    view_returns: np.ndarray,
    *,
    risk_aversion: float = 2.5,
    tau: float = 0.05,
    omega: np.ndarray | None = None,
    risk_free_rate: float = 0.0,
    allow_short: bool = False,
) -> np.ndarray:
    """Generate portfolio weights from Black–Litterman posterior inputs."""
    posterior_returns, posterior_covariance = black_litterman_posterior(
        covariance,
        market_weights,
        pick_matrix,
        view_returns,
        risk_aversion=risk_aversion,
        tau=tau,
        omega=omega,
    )

    return maximum_sharpe_weights(
        posterior_returns,
        posterior_covariance,
        risk_free_rate=risk_free_rate,
        allow_short=allow_short,
    )
