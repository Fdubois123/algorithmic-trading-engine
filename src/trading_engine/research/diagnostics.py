from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True, frozen=True)
class DrawdownDiagnostics:
    """Drawdown diagnostics for an equity curve."""

    maximum_drawdown: float
    maximum_drawdown_duration: int
    current_drawdown: float
    current_drawdown_duration: int


@dataclass(slots=True, frozen=True)
class CostDiagnostics:
    """Transaction-cost diagnostics for a research run."""

    total_cost: float
    average_cost: float
    maximum_cost: float
    total_turnover: float
    average_turnover: float
    cost_to_gross_return_ratio: float


def _validate_numeric_series(
    values: pd.Series,
    *,
    name: str,
    allow_empty: bool = False,
) -> pd.Series:
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas Series.")

    if values.empty and not allow_empty:
        raise ValueError(f"{name} cannot be empty.")

    try:
        result = values.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must contain numeric values.") from error

    array = result.to_numpy(dtype=float)

    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values.")

    return result


def equity_drawdown(
    equity_curve: pd.Series,
) -> pd.Series:
    """Calculate drawdown from the running equity peak."""
    equity = _validate_numeric_series(
        equity_curve,
        name="equity_curve",
    )

    if (equity <= 0).any():
        raise ValueError("equity_curve must contain strictly positive values.")

    running_peak = equity.cummax()

    result = equity / running_peak - 1.0

    result.name = "drawdown"

    return result


def drawdown_duration(
    equity_curve: pd.Series,
) -> pd.Series:
    """Calculate consecutive periods spent below the running peak."""
    drawdown = equity_drawdown(equity_curve)

    durations = pd.Series(
        0,
        index=drawdown.index,
        dtype=int,
        name="drawdown_duration",
    )

    current = 0

    for position, value in enumerate(drawdown):
        if value < -1e-15:
            current += 1
        else:
            current = 0

        durations.iloc[position] = current

    return durations


def summarize_drawdown(
    equity_curve: pd.Series,
) -> DrawdownDiagnostics:
    """Summarize drawdown severity and duration."""
    drawdown = equity_drawdown(equity_curve)

    duration = drawdown_duration(equity_curve)

    return DrawdownDiagnostics(
        maximum_drawdown=float(drawdown.min()),
        maximum_drawdown_duration=int(duration.max()),
        current_drawdown=float(drawdown.iloc[-1]),
        current_drawdown_duration=int(duration.iloc[-1]),
    )


def rolling_annualized_volatility(
    returns: pd.Series,
    *,
    window: int = 20,
    periods_per_year: int = 252,
) -> pd.Series:
    """Calculate rolling annualized volatility."""
    values = _validate_numeric_series(
        returns,
        name="returns",
    )

    if isinstance(window, bool) or not isinstance(
        window,
        int,
    ):
        raise TypeError("window must be an integer.")

    if window < 2:
        raise ValueError("window must be at least 2.")

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

    result = values.rolling(
        window=window,
        min_periods=window,
    ).std(ddof=1) * math.sqrt(periods_per_year)

    result.name = "rolling_annualized_volatility"

    return result


def rolling_sharpe_ratio(
    returns: pd.Series,
    *,
    window: int = 20,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    """Calculate trailing annualized Sharpe ratio."""
    values = _validate_numeric_series(
        returns,
        name="returns",
    )

    if isinstance(window, bool) or not isinstance(
        window,
        int,
    ):
        raise TypeError("window must be an integer.")

    if window < 2:
        raise ValueError("window must be at least 2.")

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

    if isinstance(
        risk_free_rate,
        bool,
    ) or not isinstance(
        risk_free_rate,
        (int, float),
    ):
        raise TypeError("risk_free_rate must be numeric.")

    risk_free_rate = float(risk_free_rate)

    if not math.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite.")

    periodic_risk_free = risk_free_rate / periods_per_year

    excess = values - periodic_risk_free

    rolling_mean = excess.rolling(
        window=window,
        min_periods=window,
    ).mean()

    rolling_std = excess.rolling(
        window=window,
        min_periods=window,
    ).std(ddof=1)

    result = (
        rolling_mean
        / rolling_std.replace(
            0.0,
            np.nan,
        )
        * math.sqrt(periods_per_year)
    )

    result.name = "rolling_sharpe_ratio"

    return result


def cost_diagnostics(
    *,
    transaction_costs: pd.Series,
    turnover: pd.Series,
    gross_returns: pd.Series,
) -> CostDiagnostics:
    """Summarize transaction costs and turnover."""
    costs = _validate_numeric_series(
        transaction_costs,
        name="transaction_costs",
    )

    turnover_values = _validate_numeric_series(
        turnover,
        name="turnover",
    )

    gross = _validate_numeric_series(
        gross_returns,
        name="gross_returns",
    )

    if not (
        costs.index.equals(turnover_values.index) and costs.index.equals(gross.index)
    ):
        raise ValueError(
            "transaction_costs, turnover and gross_returns must have matching indexes."
        )

    if (costs < 0).any():
        raise ValueError("transaction_costs cannot be negative.")

    if (turnover_values < 0).any():
        raise ValueError("turnover cannot be negative.")

    total_cost = float(costs.sum())

    gross_total = float(gross.sum())

    denominator = abs(gross_total)

    if denominator <= 1e-15:
        ratio = 0.0
    else:
        ratio = total_cost / denominator

    return CostDiagnostics(
        total_cost=total_cost,
        average_cost=float(costs.mean()),
        maximum_cost=float(costs.max()),
        total_turnover=float(turnover_values.sum()),
        average_turnover=float(turnover_values.mean()),
        cost_to_gross_return_ratio=float(ratio),
    )
