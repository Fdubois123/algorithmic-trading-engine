from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from trading_engine.research.attribution import (
    contribution_totals,
)
from trading_engine.research.benchmark import (
    BenchmarkComparison,
    compare_to_benchmark,
)
from trading_engine.research.regime_analysis import (
    regime_return_table,
)
from trading_engine.research.result import (
    ResearchResult,
)


@dataclass(slots=True, frozen=True)
class ExperimentSummary:
    """Compact summary of one research experiment."""

    final_equity: float
    total_return: float
    total_transaction_cost: float
    average_turnover: float
    benchmark: BenchmarkComparison | None
    strategy_contributions: pd.Series
    regime_performance: pd.DataFrame


def build_experiment_summary(
    *,
    result: ResearchResult,
    strategy_returns: pd.DataFrame,
    benchmark_returns: pd.Series | None = None,
) -> ExperimentSummary:
    """Build benchmark, attribution and regime analysis for a run."""
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

    strategy_contributions = contribution_totals(
        strategy_returns,
        result.applied_weights,
    )

    if benchmark_returns is None:
        benchmark = None

    else:
        benchmark = compare_to_benchmark(
            result.returns,
            benchmark_returns,
        )

    regime_table = regime_return_table(
        result.returns,
        result.regime_frame["market_regime"],
    )

    return ExperimentSummary(
        final_equity=result.final_equity,
        total_return=result.total_return,
        total_transaction_cost=(result.total_transaction_cost),
        average_turnover=(result.average_turnover),
        benchmark=benchmark,
        strategy_contributions=(strategy_contributions),
        regime_performance=regime_table,
    )
