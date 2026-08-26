from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True, frozen=True)
class MeanReversionResult:
    """Mean-reversion characteristics of a spread."""

    autoregressive_coefficient: float
    mean_reversion_speed: float
    half_life: float
    long_run_mean: float
    observations: int


def _validate_spread(
    spread: pd.Series,
    *,
    minimum_observations: int = 3,
) -> pd.Series:
    if not isinstance(
        spread,
        pd.Series,
    ):
        raise TypeError("spread must be a pandas Series.")

    if spread.empty:
        raise ValueError("spread cannot be empty.")

    if len(spread) < minimum_observations:
        raise ValueError("spread does not contain enough observations.")

    try:
        values = spread.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("spread must contain numeric values.") from error

    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("spread must contain only finite values.")

    return values


def estimate_mean_reversion(
    spread: pd.Series,
) -> MeanReversionResult:
    """Estimate AR(1) mean-reversion characteristics."""
    values = _validate_spread(
        spread,
        minimum_observations=3,
    ).to_numpy(dtype=float)

    lagged = values[:-1]
    current = values[1:]

    if np.var(lagged) <= 1e-15:
        raise ValueError("spread must have non-zero lagged variance.")

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
        current,
        rcond=None,
    )

    intercept = float(coefficients[0])

    phi = float(coefficients[1])

    if not math.isfinite(phi):
        raise ValueError("autoregressive coefficient must be finite.")

    if not 0 < phi < 1:
        raise ValueError("spread does not exhibit stable positive mean reversion.")

    mean_reversion_speed = -math.log(phi)

    half_life = math.log(2.0) / mean_reversion_speed

    long_run_mean = intercept / (1.0 - phi)

    return MeanReversionResult(
        autoregressive_coefficient=phi,
        mean_reversion_speed=mean_reversion_speed,
        half_life=half_life,
        long_run_mean=long_run_mean,
        observations=len(values),
    )


def estimate_half_life(
    spread: pd.Series,
) -> float:
    """Return estimated spread half-life."""
    return estimate_mean_reversion(spread).half_life
