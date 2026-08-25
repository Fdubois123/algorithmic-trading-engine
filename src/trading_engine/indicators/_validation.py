from __future__ import annotations

import numpy as np
import pandas as pd


def validate_numeric_series(
    series: pd.Series,
    *,
    name: str = "Series",
    allow_nan: bool = False,
) -> None:
    """Validate a numeric pandas Series.

    Args:
        series: Series to validate.
        name: Human-readable name used in error messages.
        allow_nan: Whether missing values are permitted.

    Raises:
        TypeError: If the object is not a pandas Series or is non-numeric.
        ValueError: If the Series is empty, contains forbidden missing
            values, or contains non-finite values.
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series.")

    if series.empty:
        raise ValueError(f"{name} cannot be empty.")

    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must contain numeric values.")

    if not allow_nan and series.isna().any():
        raise ValueError(f"{name} cannot contain missing values.")

    finite_values = series.dropna().to_numpy(dtype=float)

    if not np.isfinite(finite_values).all():
        raise ValueError(f"{name} must contain only finite values.")


def validate_positive_series(
    series: pd.Series,
    *,
    name: str = "Series",
) -> None:
    """Validate a strictly positive numeric Series."""
    validate_numeric_series(series, name=name)

    if (series <= 0).any():
        raise ValueError(f"{name} must be strictly positive.")


def validate_window(
    window: int,
    *,
    name: str = "Window",
) -> None:
    """Validate a rolling-window parameter."""
    if isinstance(window, bool) or not isinstance(window, int):
        raise TypeError(f"{name} must be an integer.")

    if window <= 0:
        raise ValueError(f"{name} must be greater than zero.")
