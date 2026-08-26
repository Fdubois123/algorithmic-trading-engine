from __future__ import annotations

import math

import numpy as np


def validate_covariance_matrix(
    covariance: np.ndarray,
) -> np.ndarray:
    """Validate and return a covariance matrix as float ndarray."""
    matrix = np.asarray(
        covariance,
        dtype=float,
    )

    if matrix.ndim != 2:
        raise ValueError("covariance must be a two-dimensional matrix.")

    rows, columns = matrix.shape

    if rows == 0:
        raise ValueError("covariance cannot be empty.")

    if rows != columns:
        raise ValueError("covariance must be square.")

    if not np.isfinite(matrix).all():
        raise ValueError("covariance must contain only finite values.")

    if not np.allclose(
        matrix,
        matrix.T,
        rtol=1e-10,
        atol=1e-12,
    ):
        raise ValueError("covariance must be symmetric.")

    diagonal = np.diag(matrix)

    if np.any(diagonal < 0):
        raise ValueError("covariance diagonal cannot be negative.")

    eigenvalues = np.linalg.eigvalsh(matrix)

    if np.min(eigenvalues) < -1e-10:
        raise ValueError("covariance must be positive semidefinite.")

    return matrix


def validate_expected_returns(
    expected_returns: np.ndarray,
    *,
    number_of_assets: int | None = None,
) -> np.ndarray:
    """Validate an expected-return vector."""
    values = np.asarray(
        expected_returns,
        dtype=float,
    )

    if values.ndim != 1:
        raise ValueError("expected_returns must be one-dimensional.")

    if values.size == 0:
        raise ValueError("expected_returns cannot be empty.")

    if not np.isfinite(values).all():
        raise ValueError("expected_returns must contain only finite values.")

    if number_of_assets is not None and values.size != number_of_assets:
        raise ValueError("expected_returns length must match the number of assets.")

    return values


def validate_weights(
    weights: np.ndarray,
    *,
    number_of_assets: int | None = None,
    require_fully_invested: bool = True,
    allow_short: bool = False,
) -> np.ndarray:
    """Validate portfolio weights."""
    values = np.asarray(
        weights,
        dtype=float,
    )

    if values.ndim != 1:
        raise ValueError("weights must be one-dimensional.")

    if values.size == 0:
        raise ValueError("weights cannot be empty.")

    if not np.isfinite(values).all():
        raise ValueError("weights must contain only finite values.")

    if number_of_assets is not None and values.size != number_of_assets:
        raise ValueError("weights length must match the number of assets.")

    if not allow_short and np.any(values < -1e-12):
        raise ValueError("negative weights are not allowed.")

    if require_fully_invested and not math.isclose(
        float(values.sum()),
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        raise ValueError("weights must sum to 1.")

    return values
