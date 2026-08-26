from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True, frozen=True)
class BenchmarkComparison:
    """Performance comparison between research portfolio and benchmark."""

    portfolio_total_return: float
    benchmark_total_return: float
    excess_total_return: float
    portfolio_volatility: float
    benchmark_volatility: float
    tracking_error: float
    information_ratio: float


def _validate_return_series(
    returns: pd.Series,
    *,
    name: str,
) -> pd.Series:
    if not isinstance(
        returns,
        pd.Series,
    ):
        raise TypeError(f"{name} must be a pandas Series.")

    if returns.empty:
        raise ValueError(f"{name} cannot be empty.")

    try:
        values = returns.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must contain numeric values.") from error

    array = values.to_numpy(dtype=float)

    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values.")

    return values


def cumulative_return(
    returns: pd.Series,
) -> float:
    """Return compounded total return."""
    values = _validate_return_series(
        returns,
        name="returns",
    )

    return float((1.0 + values).prod() - 1.0)


def annualized_standard_deviation(
    returns: pd.Series,
    *,
    periods_per_year: int = 252,
) -> float:
    """Return annualized sample standard deviation."""
    values = _validate_return_series(
        returns,
        name="returns",
    )

    if isinstance(
        periods_per_year,
        bool,
    ) or not isinstance(
        periods_per_year,
        int,
    ):
        raise TypeError("periods_per_year must be an integer.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")

    if len(values) < 2:
        return 0.0

    return float(values.std(ddof=1) * math.sqrt(periods_per_year))


def compare_to_benchmark(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    periods_per_year: int = 252,
) -> BenchmarkComparison:
    """Compare portfolio returns against a benchmark."""
    portfolio = _validate_return_series(
        portfolio_returns,
        name="portfolio_returns",
    )

    benchmark = _validate_return_series(
        benchmark_returns,
        name="benchmark_returns",
    )

    if not portfolio.index.equals(benchmark.index):
        raise ValueError(
            "portfolio_returns and benchmark_returns must have matching indexes."
        )

    portfolio_total = cumulative_return(portfolio)

    benchmark_total = cumulative_return(benchmark)

    active_returns = portfolio - benchmark

    portfolio_volatility = annualized_standard_deviation(
        portfolio,
        periods_per_year=periods_per_year,
    )

    benchmark_volatility = annualized_standard_deviation(
        benchmark,
        periods_per_year=periods_per_year,
    )

    tracking_error = annualized_standard_deviation(
        active_returns,
        periods_per_year=periods_per_year,
    )

    if tracking_error <= 1e-15:
        information_ratio = 0.0
    else:
        annualized_active_return = float(active_returns.mean() * periods_per_year)

        information_ratio = annualized_active_return / tracking_error

    return BenchmarkComparison(
        portfolio_total_return=portfolio_total,
        benchmark_total_return=benchmark_total,
        excess_total_return=(portfolio_total - benchmark_total),
        portfolio_volatility=portfolio_volatility,
        benchmark_volatility=benchmark_volatility,
        tracking_error=tracking_error,
        information_ratio=float(information_ratio),
    )
