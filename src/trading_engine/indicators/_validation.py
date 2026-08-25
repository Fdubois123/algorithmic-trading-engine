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


def validate_pair(
    left: pd.Series,
    right: pd.Series,
    *,
    left_name: str = "Left series",
    right_name: str = "Right series",
    allow_nan: bool = True,
) -> None:
    """Validate two aligned numeric pandas Series.

    Args:
        left: First numeric Series.
        right: Second numeric Series.
        left_name: Name used in error messages for the first Series.
        right_name: Name used in error messages for the second Series.
        allow_nan: Whether missing values are permitted.

    Raises:
        TypeError: If either input is invalid.
        ValueError: If either Series is empty, contains invalid values,
            or the indices do not match exactly.
    """
    validate_numeric_series(
        left,
        name=left_name,
        allow_nan=allow_nan,
    )

    validate_numeric_series(
        right,
        name=right_name,
        allow_nan=allow_nan,
    )

    if not left.index.equals(right.index):
        raise ValueError("Series indices must match exactly.")
