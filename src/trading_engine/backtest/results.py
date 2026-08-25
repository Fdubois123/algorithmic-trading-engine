from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from trading_engine.backtest.models import Fill
from trading_engine.performance import (
    annualized_return,
    calmar_ratio,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
)


@dataclass(slots=True, frozen=True)
class BacktestResult:
    equity_curve: pd.Series
    fills: tuple[Fill, ...]
    periods_per_year: int = 252

    @property
    def returns(self) -> pd.Series:
        result = self.equity_curve.pct_change(fill_method=None)
        result.name = "returns"

        return result

    @property
    def total_return(self) -> float:
        if self.equity_curve.empty:
            return 0.0

        return float(self.equity_curve.iloc[-1] / self.equity_curve.iloc[0] - 1.0)

    @property
    def maximum_drawdown(self) -> float:
        return max_drawdown(self.equity_curve)

    def metrics(self) -> dict[str, float]:
        clean_returns = self.returns.dropna()

        if clean_returns.empty:
            return {
                "total_return": self.total_return,
                "max_drawdown": self.maximum_drawdown,
            }

        return {
            "total_return": self.total_return,
            "annualized_return": annualized_return(
                clean_returns,
                periods_per_year=self.periods_per_year,
            ),
            "sharpe_ratio": sharpe_ratio(
                clean_returns,
                periods_per_year=self.periods_per_year,
            ),
            "sortino_ratio": sortino_ratio(
                clean_returns,
                periods_per_year=self.periods_per_year,
            ),
            "max_drawdown": self.maximum_drawdown,
            "calmar_ratio": calmar_ratio(
                clean_returns,
                periods_per_year=self.periods_per_year,
            ),
        }
