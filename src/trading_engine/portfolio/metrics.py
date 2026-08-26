from __future__ import annotations

import math

import numpy as np

from trading_engine.portfolio.optimization import (
    portfolio_volatility,
)
from trading_engine.portfolio.risk_parity import (
    percentage_risk_contributions,
)
from trading_engine.portfolio.validation import (
    validate_covariance_matrix,
    validate_weights,
)


def weight_concentration(
    weights: np.ndarray,
) -> float:
    """Return the Herfindahl concentration index of portfolio weights."""
    allocation = validate_weights(
        weights,
        allow_short=False,
    )

    return float(np.square(allocation).sum())


def effective_number_of_assets(
    weights: np.ndarray,
) -> float:
    """Return inverse Herfindahl concentration."""
    concentration = weight_concentration(weights)

    if concentration <= 0:
        return 0.0

    return float(1.0 / concentration)


def diversification_ratio(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Return weighted standalone volatility divided by portfolio volatility."""
    matrix = validate_covariance_matrix(covariance)

    allocation = validate_weights(
        weights,
        number_of_assets=matrix.shape[0],
        allow_short=False,
    )

    asset_volatility = np.sqrt(
        np.maximum(
            np.diag(matrix),
            0.0,
        )
    )

    numerator = float(allocation @ asset_volatility)

    denominator = portfolio_volatility(
        allocation,
        matrix,
    )

    if denominator <= 1e-15:
        return 0.0

    return float(numerator / denominator)


def risk_concentration(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Return Herfindahl concentration of percentage risk contributions."""
    contributions = percentage_risk_contributions(
        weights,
        covariance,
    )

    return float(np.square(contributions).sum())


def effective_number_of_risk_bets(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Return inverse concentration of portfolio risk contributions."""
    concentration = risk_concentration(
        weights,
        covariance,
    )

    if concentration <= 0:
        return 0.0

    return float(1.0 / concentration)


def diversification_gain(
    weights: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Return standalone weighted volatility minus portfolio volatility."""
    matrix = validate_covariance_matrix(covariance)

    allocation = validate_weights(
        weights,
        number_of_assets=matrix.shape[0],
        allow_short=False,
    )

    standalone_volatility = float(
        allocation
        @ np.sqrt(
            np.maximum(
                np.diag(matrix),
                0.0,
            )
        )
    )

    portfolio_risk = portfolio_volatility(
        allocation,
        matrix,
    )

    gain = standalone_volatility - portfolio_risk

    if not math.isfinite(gain):
        raise ValueError("diversification gain must be finite.")

    return float(
        max(
            gain,
            0.0,
        )
    )
