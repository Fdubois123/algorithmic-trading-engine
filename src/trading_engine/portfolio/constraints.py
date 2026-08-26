from __future__ import annotations

import math

import numpy as np

from trading_engine.portfolio.validation import (
    validate_covariance_matrix,
    validate_weights,
)


def _expand_bound(
    value: float | np.ndarray,
    *,
    number_of_assets: int,
    name: str,
) -> np.ndarray:
    array = np.asarray(
        value,
        dtype=float,
    )

    if array.ndim == 0:
        array = np.full(
            number_of_assets,
            float(array),
            dtype=float,
        )

    if array.ndim != 1:
        raise ValueError(f"{name} must be scalar or one-dimensional.")

    if array.size != number_of_assets:
        raise ValueError(f"{name} length must match the number of assets.")

    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values.")

    return array


def validate_weight_bounds(
    *,
    lower_bounds: float | np.ndarray,
    upper_bounds: float | np.ndarray,
    number_of_assets: int,
    target_sum: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate portfolio box constraints."""
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

    if isinstance(
        target_sum,
        bool,
    ) or not isinstance(
        target_sum,
        (int, float),
    ):
        raise TypeError("target_sum must be numeric.")

    target_sum = float(target_sum)

    if not math.isfinite(target_sum):
        raise ValueError("target_sum must be finite.")

    lower = _expand_bound(
        lower_bounds,
        number_of_assets=number_of_assets,
        name="lower_bounds",
    )

    upper = _expand_bound(
        upper_bounds,
        number_of_assets=number_of_assets,
        name="upper_bounds",
    )

    if np.any(lower > upper):
        raise ValueError("lower_bounds cannot exceed upper_bounds.")

    if float(lower.sum()) > target_sum + 1e-12:
        raise ValueError("lower bounds make the target sum infeasible.")

    if float(upper.sum()) < target_sum - 1e-12:
        raise ValueError("upper bounds make the target sum infeasible.")

    return lower, upper


def project_weights_to_bounded_simplex(
    weights: np.ndarray,
    *,
    lower_bounds: float | np.ndarray = 0.0,
    upper_bounds: float | np.ndarray = 1.0,
    target_sum: float = 1.0,
    tolerance: float = 1e-12,
    max_iterations: int = 200,
) -> np.ndarray:
    """Project weights onto box constraints and a fixed-sum simplex."""
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

    lower, upper = validate_weight_bounds(
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        number_of_assets=values.size,
        target_sum=target_sum,
    )

    low_lambda = float(np.min(values - upper))

    high_lambda = float(np.max(values - lower))

    projected = np.clip(
        values,
        lower,
        upper,
    )

    for _ in range(max_iterations):
        multiplier = (low_lambda + high_lambda) / 2.0

        projected = np.clip(
            values - multiplier,
            lower,
            upper,
        )

        total = float(projected.sum())

        if abs(total - target_sum) <= tolerance:
            return projected

        if total > target_sum:
            low_lambda = multiplier
        else:
            high_lambda = multiplier

    if abs(float(projected.sum()) - target_sum) <= max(
        tolerance,
        1e-10,
    ):
        return projected

    raise RuntimeError("bounded-simplex projection failed to converge.")


def portfolio_turnover(
    current_weights: np.ndarray,
    target_weights: np.ndarray,
) -> float:
    """Return one-way portfolio turnover."""
    current = validate_weights(
        current_weights,
        allow_short=True,
    )

    target = validate_weights(
        target_weights,
        number_of_assets=current.size,
        allow_short=True,
    )

    return float(0.5 * np.abs(target - current).sum())


def enforce_turnover_limit(
    current_weights: np.ndarray,
    target_weights: np.ndarray,
    *,
    max_turnover: float,
) -> np.ndarray:
    """Scale a rebalance so it does not exceed a turnover budget."""
    current = validate_weights(
        current_weights,
        allow_short=True,
    )

    target = validate_weights(
        target_weights,
        number_of_assets=current.size,
        allow_short=True,
    )

    if isinstance(
        max_turnover,
        bool,
    ) or not isinstance(
        max_turnover,
        (int, float),
    ):
        raise TypeError("max_turnover must be numeric.")

    max_turnover = float(max_turnover)

    if not math.isfinite(max_turnover):
        raise ValueError("max_turnover must be finite.")

    if max_turnover < 0:
        raise ValueError("max_turnover cannot be negative.")

    turnover = portfolio_turnover(
        current,
        target,
    )

    if turnover <= max_turnover:
        return target.copy()

    if max_turnover == 0:
        return current.copy()

    fraction = max_turnover / turnover

    result = current + fraction * (target - current)

    return result


def bounded_minimum_variance_weights(
    covariance: np.ndarray,
    *,
    lower_bounds: float | np.ndarray = 0.0,
    upper_bounds: float | np.ndarray = 1.0,
    tolerance: float = 1e-10,
    max_iterations: int = 10_000,
) -> np.ndarray:
    """Solve long/box-constrained minimum variance by projected gradient."""
    matrix = validate_covariance_matrix(covariance)

    asset_count = matrix.shape[0]

    lower, upper = validate_weight_bounds(
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        number_of_assets=asset_count,
    )

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

    weights = project_weights_to_bounded_simplex(
        np.full(
            asset_count,
            1.0 / asset_count,
        ),
        lower_bounds=lower,
        upper_bounds=upper,
    )

    largest_eigenvalue = float(np.max(np.linalg.eigvalsh(matrix)))

    if largest_eigenvalue <= 1e-15:
        return weights

    step_size = 1.0 / (2.0 * largest_eigenvalue)

    for _ in range(max_iterations):
        gradient = 2.0 * matrix @ weights

        candidate = weights - step_size * gradient

        candidate = project_weights_to_bounded_simplex(
            candidate,
            lower_bounds=lower,
            upper_bounds=upper,
        )

        if np.max(np.abs(candidate - weights)) <= tolerance:
            return candidate

        weights = candidate

    raise RuntimeError("bounded minimum-variance optimization failed to converge.")
