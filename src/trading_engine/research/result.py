from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True, frozen=True)
class ResearchResult:
    """Output of a complete quantitative research experiment."""

    equity_curve: pd.Series
    returns: pd.Series
    gross_returns: pd.Series
    regime_frame: pd.DataFrame
    target_weights: pd.DataFrame
    applied_weights: pd.DataFrame
    turnover: pd.Series
    transaction_costs: pd.Series

    @property
    def observations(self) -> int:
        return len(self.returns)

    @property
    def final_equity(self) -> float:
        if self.equity_curve.empty:
            return 1.0

        return float(self.equity_curve.iloc[-1])

    @property
    def total_return(self) -> float:
        return self.final_equity - 1.0

    @property
    def total_transaction_cost(self) -> float:
        return float(self.transaction_costs.sum())

    @property
    def average_turnover(self) -> float:
        if self.turnover.empty:
            return 0.0

        return float(self.turnover.mean())
