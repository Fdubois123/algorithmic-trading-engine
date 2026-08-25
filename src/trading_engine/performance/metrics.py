from __future__ import annotations

import math

import numpy as np
import pandas as pd

from trading_engine.indicators._validation import validate_numeric_series
from trading_engine.indicators.returns import wealth_index
from trading_engine.performance.drawdown import max_drawdown


def _validate_periods_per_year(periods_per_year: int) -> None:
    if isinstance(periods_per_year, bool) or not isinstance(
        periods_per_year,
        int,
    ):
        raise TypeError("periods_per_year must be an integer.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")


def annualized_return(
    returns: pd.Series,
    *,
    periods_per_year: int = 252,
) -> float:
    """Calculate geometrically annualized return."""
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    _validate_periods_per_year(periods_per_year)

    clean = returns.dropna()

    if clean.empty:
        raise ValueError("Returns contain no valid observations.")

    if (clean <= -1.0).any():
        raise ValueError("Returns must be greater than -100%.")

    growth = float((1.0 + clean).prod())
    years = len(clean) / periods_per_year

    return growth ** (1.0 / years) - 1.0


def cagr(
    initial_value: float,
    final_value: float,
    years: float,
) -> float:
    """Calculate compound annual growth rate."""
    for name, value in {
        "initial_value": initial_value,
        "final_value": final_value,
        "years": years,
    }.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be numeric.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")

    if initial_value <= 0:
        raise ValueError("initial_value must be greater than zero.")

    if final_value <= 0:
        raise ValueError("final_value must be greater than zero.")

    if years <= 0:
        raise ValueError("years must be greater than zero.")

    return (final_value / initial_value) ** (1.0 / years) - 1.0


def sharpe_ratio(
    returns: pd.Series,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> float:
    """Calculate annualized Sharpe ratio."""
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    _validate_periods_per_year(periods_per_year)

    if not isinstance(risk_free_rate, (int, float)) or isinstance(
        risk_free_rate,
        bool,
    ):
        raise TypeError("risk_free_rate must be numeric.")

    if not math.isfinite(float(risk_free_rate)):
        raise ValueError("risk_free_rate must be finite.")

    clean = returns.dropna()

    if clean.empty:
        raise ValueError("Returns contain no valid observations.")

    periodic_rf = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0

    excess = clean - periodic_rf
    volatility = excess.std(ddof=ddof)

    if volatility == 0 or np.isnan(volatility):
        return float("nan")

    return float(excess.mean() / volatility * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: pd.Series,
    *,
    target_return: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Calculate annualized Sortino ratio."""
    validate_numeric_series(
        returns,
        name="Returns",
        allow_nan=True,
    )
    _validate_periods_per_year(periods_per_year)

    if not isinstance(target_return, (int, float)) or isinstance(
        target_return,
        bool,
    ):
        raise TypeError("target_return must be numeric.")

    if not math.isfinite(float(target_return)):
        raise ValueError("target_return must be finite.")

    clean = returns.dropna()

    if clean.empty:
        raise ValueError("Returns contain no valid observations.")

    periodic_target = (1.0 + target_return) ** (1.0 / periods_per_year) - 1.0

    excess = clean - periodic_target
    downside = np.minimum(excess, 0.0)

    downside_deviation = np.sqrt(np.mean(np.square(downside)))

    if downside_deviation == 0:
        return float("nan")

    return float(excess.mean() / downside_deviation * np.sqrt(periods_per_year))


def calmar_ratio(
    returns: pd.Series,
    *,
    periods_per_year: int = 252,
) -> float:
    """Calculate annualized return divided by absolute maximum drawdown."""
    ann_return = annualized_return(
        returns,
        periods_per_year=periods_per_year,
    )

    wealth = wealth_index(
        returns.fillna(0.0),
        initial_capital=1.0,
    )

    mdd = abs(max_drawdown(wealth))

    if mdd == 0:
        return float("nan")

    return ann_return / mdd


def tracking_error(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> float:
    """Calculate annualized tracking error."""
    validate_numeric_series(
        portfolio_returns,
        name="Portfolio returns",
        allow_nan=True,
    )
    validate_numeric_series(
        benchmark_returns,
        name="Benchmark returns",
        allow_nan=True,
    )

    _validate_periods_per_year(periods_per_year)

    if not portfolio_returns.index.equals(benchmark_returns.index):
        raise ValueError("Return series indices must match exactly.")

    active = portfolio_returns - benchmark_returns
    clean = active.dropna()

    if clean.empty:
        raise ValueError("Active returns contain no valid observations.")

    return float(clean.std(ddof=ddof) * np.sqrt(periods_per_year))


def information_ratio(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> float:
    """Calculate annualized information ratio."""
    validate_numeric_series(
        portfolio_returns,
        name="Portfolio returns",
        allow_nan=True,
    )
    validate_numeric_series(
        benchmark_returns,
        name="Benchmark returns",
        allow_nan=True,
    )

    if not portfolio_returns.index.equals(benchmark_returns.index):
        raise ValueError("Return series indices must match exactly.")

    active = (portfolio_returns - benchmark_returns).dropna()

    if active.empty:
        raise ValueError("Active returns contain no valid observations.")

    error = tracking_error(
        portfolio_returns,
        benchmark_returns,
        periods_per_year=periods_per_year,
        ddof=ddof,
    )

    if error == 0 or np.isnan(error):
        return float("nan")

    annualized_active_return = active.mean() * periods_per_year

    return float(annualized_active_return / error)
