from trading_engine.research.attribution import (
    StrategyAttribution,
    contribution_totals,
    strategy_attribution,
    strategy_contribution_frame,
)
from trading_engine.research.benchmark import (
    BenchmarkComparison,
    annualized_standard_deviation,
    compare_to_benchmark,
    cumulative_return,
)
from trading_engine.research.config import (
    ResearchConfig,
)
from trading_engine.research.diagnostics import (
    CostDiagnostics,
    DrawdownDiagnostics,
    cost_diagnostics,
    drawdown_duration,
    equity_drawdown,
    rolling_annualized_volatility,
    rolling_sharpe_ratio,
    summarize_drawdown,
)
from trading_engine.research.metadata import (
    ExperimentMetadata,
    build_experiment_metadata,
    config_fingerprint,
    experiment_identifier,
)
from trading_engine.research.rankings import (
    RegimeRanking,
    StrategyRanking,
    rank_regimes,
    rank_strategies,
    regime_ranking_table,
    strategy_ranking_table,
)
from trading_engine.research.regime_analysis import (
    RegimePerformance,
    regime_performance,
    regime_return_table,
)
from trading_engine.research.reporting import (
    ResearchReport,
    build_research_report,
)
from trading_engine.research.result import (
    ResearchResult,
)
from trading_engine.research.runner import (
    run_research_experiment,
)
from trading_engine.research.serialization import (
    dataframe_to_records,
    export_research_bundle,
    research_report_to_dict,
    research_result_to_dict,
    series_to_records,
)
from trading_engine.research.summary import (
    ExperimentSummary,
    build_experiment_summary,
)

__all__ = [
    "BenchmarkComparison",
    "CostDiagnostics",
    "DrawdownDiagnostics",
    "ExperimentMetadata",
    "ExperimentSummary",
    "RegimePerformance",
    "RegimeRanking",
    "ResearchConfig",
    "ResearchReport",
    "ResearchResult",
    "StrategyAttribution",
    "StrategyRanking",
    "annualized_standard_deviation",
    "build_experiment_metadata",
    "build_experiment_summary",
    "build_research_report",
    "compare_to_benchmark",
    "config_fingerprint",
    "contribution_totals",
    "cost_diagnostics",
    "cumulative_return",
    "dataframe_to_records",
    "drawdown_duration",
    "equity_drawdown",
    "experiment_identifier",
    "export_research_bundle",
    "rank_regimes",
    "rank_strategies",
    "regime_performance",
    "regime_ranking_table",
    "regime_return_table",
    "research_report_to_dict",
    "research_result_to_dict",
    "rolling_annualized_volatility",
    "rolling_sharpe_ratio",
    "run_research_experiment",
    "series_to_records",
    "strategy_attribution",
    "strategy_contribution_frame",
    "strategy_ranking_table",
    "summarize_drawdown",
]
