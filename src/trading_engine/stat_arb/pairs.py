from __future__ import annotations

import numpy as np
import pandas as pd


def validate_price_series(
    prices: pd.Series,
    *,
    name: str = "prices",
    minimum_observations: int = 2,
) -> pd.Series:
    """Validate a price series used by statistical-arbitrage models."""
    if not isinstance(prices, pd.Series):
        raise TypeError(f"{name} must be a pandas Series.")

    if isinstance(
        minimum_observations,
        bool,
    ) or not isinstance(
        minimum_observations,
        int,
    ):
        raise TypeError("minimum_observations must be an integer.")

    if minimum_observations <= 0:
        raise ValueError("minimum_observations must be greater than zero.")

    if prices.empty:
        raise ValueError(f"{name} cannot be empty.")

    if len(prices) < minimum_observations:
        raise ValueError(
            f"{name} must contain at least {minimum_observations} observations."
        )

    try:
        values = prices.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must contain numeric values.") from error

    array = values.to_numpy(dtype=float)

    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values.")

    if np.any(array <= 0):
        raise ValueError(f"{name} must contain strictly positive prices.")

    if not values.index.is_unique:
        raise ValueError(f"{name} index must not contain duplicates.")

    if not values.index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be sorted.")

    return values


def align_pair_prices(
    first: pd.Series,
    second: pd.Series,
    *,
    first_name: str = "first",
    second_name: str = "second",
    minimum_observations: int = 2,
) -> pd.DataFrame:
    """Align two price series on their common observations."""
    first_values = validate_price_series(
        first,
        name=first_name,
        minimum_observations=minimum_observations,
    )

    second_values = validate_price_series(
        second,
        name=second_name,
        minimum_observations=minimum_observations,
    )

    aligned = pd.concat(
        [
            first_values.rename(first_name),
            second_values.rename(second_name),
        ],
        axis=1,
        join="inner",
    ).dropna()

    if len(aligned) < minimum_observations:
        raise ValueError(
            "aligned pair must contain at least "
            f"{minimum_observations} common observations."
        )

    return aligned


def pair_log_returns(
    first: pd.Series,
    second: pd.Series,
    *,
    first_name: str = "first",
    second_name: str = "second",
) -> pd.DataFrame:
    """Return aligned log returns for two assets."""
    aligned = align_pair_prices(
        first,
        second,
        first_name=first_name,
        second_name=second_name,
        minimum_observations=2,
    )

    returns = np.log(aligned / aligned.shift(1)).dropna()

    if returns.empty:
        raise ValueError(
            "pair does not contain enough observations to calculate returns."
        )

    return returns
