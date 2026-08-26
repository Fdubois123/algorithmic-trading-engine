from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from trading_engine.research.diagnostics import (
    CostDiagnostics,
    DrawdownDiagnostics,
    cost_diagnostics,
    rolling_annualized_volatility,
    rolling_sharpe_ratio,
    summarize_drawdown,
)
from trading_engine.research.rankings import (
    regime_ranking_table,
    strategy_ranking_table,
)
from trading_engine.research.result import (
    ResearchResult,
)


@dataclass(slots=True, frozen=True)
class ResearchReport:
    """Export-ready report structure for one research run."""

    overview: pd.Series
    rolling_metrics: pd.DataFrame
    strategy_ranking: pd.DataFrame
    regime_ranking: pd.DataFrame
    drawdown: DrawdownDiagnostics
    costs: CostDiagnostics


def build_research_report(
    *,
    result: ResearchResult,
    strategy_returns: pd.DataFrame,
    rolling_window: int = 20,
    periods_per_year: int = 252,
) -> ResearchReport:
    """Build a complete research diagnostics report."""
    if not isinstance(
        result,
        ResearchResult,
    ):
        raise TypeError("result must be a ResearchResult.")

    if not isinstance(
        strategy_returns,
        pd.DataFrame,
    ):
        raise TypeError("strategy_returns must be a pandas DataFrame.")

    if not strategy_returns.index.equals(result.returns.index):
        raise ValueError("strategy_returns index must match result returns index.")

    if list(strategy_returns.columns) != list(result.applied_weights.columns):
        raise ValueError(
            "strategy_returns columns must match result applied_weights columns."
        )

    drawdown = summarize_drawdown(result.equity_curve)

    costs = cost_diagnostics(
        transaction_costs=(result.transaction_costs),
        turnover=result.turnover,
        gross_returns=(result.gross_returns),
    )

    rolling_metrics = pd.DataFrame(
        {
            "rolling_volatility": (
                rolling_annualized_volatility(
                    result.returns,
                    window=rolling_window,
                    periods_per_year=periods_per_year,
                )
            ),
            "rolling_sharpe": (
                rolling_sharpe_ratio(
                    result.returns,
                    window=rolling_window,
                    periods_per_year=periods_per_year,
                )
            ),
        },
        index=result.returns.index,
    )

    strategy_table = strategy_ranking_table(
        strategy_returns,
        result.applied_weights,
    )

    regime_table = regime_ranking_table(
        result.returns,
        result.regime_frame["market_regime"],
    )

    overview = pd.Series(
        {
            "observations": float(result.observations),
            "final_equity": (result.final_equity),
            "total_return": (result.total_return),
            "maximum_drawdown": (drawdown.maximum_drawdown),
            "maximum_drawdown_duration": float(drawdown.maximum_drawdown_duration),
            "total_transaction_cost": (costs.total_cost),
            "average_turnover": (costs.average_turnover),
        },
        dtype=float,
        name="research_overview",
    )

    return ResearchReport(
        overview=overview,
        rolling_metrics=rolling_metrics,
        strategy_ranking=strategy_table,
        regime_ranking=regime_table,
        drawdown=drawdown,
        costs=costs,
    )
