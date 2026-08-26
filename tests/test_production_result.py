import pandas as pd
import pytest

from trading_engine.production import (
    EngineResult,
)
from trading_engine.research import (
    ExperimentMetadata,
    ExperimentSummary,
    ResearchReport,
    ResearchResult,
)
from trading_engine.research.diagnostics import (
    CostDiagnostics,
    DrawdownDiagnostics,
)


def _research_result() -> ResearchResult:
    index = pd.date_range(
        "2026-01-01",
        periods=2,
        freq="D",
    )

    returns = pd.Series(
        [
            0.0,
            0.01,
        ],
        index=index,
    )

    return ResearchResult(
        equity_curve=(1.0 + returns).cumprod(),
        returns=returns,
        gross_returns=returns,
        regime_frame=pd.DataFrame(
            {
                "market_regime": [
                    "normal_vol_sideways",
                    "normal_vol_bull",
                ]
            },
            index=index,
        ),
        target_weights=pd.DataFrame(
            {
                "trend": [
                    0.0,
                    1.0,
                ]
            },
            index=index,
        ),
        applied_weights=pd.DataFrame(
            {
                "trend": [
                    0.0,
                    1.0,
                ]
            },
            index=index,
        ),
        turnover=pd.Series(
            [
                0.0,
                0.5,
            ],
            index=index,
        ),
        transaction_costs=pd.Series(
            [
                0.0,
                0.0,
            ],
            index=index,
        ),
    )


def _report() -> ResearchReport:
    return ResearchReport(
        overview=pd.Series(
            {
                "observations": 2.0,
            }
        ),
        rolling_metrics=pd.DataFrame(),
        strategy_ranking=pd.DataFrame(),
        regime_ranking=pd.DataFrame(),
        drawdown=DrawdownDiagnostics(
            maximum_drawdown=0.0,
            maximum_drawdown_duration=0,
            current_drawdown=0.0,
            current_drawdown_duration=0,
        ),
        costs=CostDiagnostics(
            total_cost=0.0,
            average_cost=0.0,
            maximum_cost=0.0,
            total_turnover=0.5,
            average_turnover=0.25,
            cost_to_gross_return_ratio=0.0,
        ),
    )


def _summary() -> ExperimentSummary:
    return ExperimentSummary(
        final_equity=1.01,
        total_return=0.01,
        total_transaction_cost=0.0,
        average_turnover=0.25,
        benchmark=None,
        strategy_contributions=pd.Series(
            {
                "trend": 0.01,
            }
        ),
        regime_performance=pd.DataFrame(),
    )


def _metadata() -> ExperimentMetadata:
    return ExperimentMetadata(
        experiment_id="experiment-id",
        config_fingerprint="fingerprint",
        created_at="2026-01-01T00:00:00+00:00",
        observations=2,
        strategy_count=1,
    )


def test_engine_result_properties():
    result = EngineResult(
        research=_research_result(),
        report=_report(),
        summary=_summary(),
        metadata=_metadata(),
        benchmark_name="SPY",
        experiment_name="test",
    )

    assert result.final_equity == pytest.approx(1.01)

    assert result.total_return == pytest.approx(0.01)

    assert result.observations == 2

    assert result.experiment_id == "experiment-id"


def test_engine_result_preserves_names():
    result = EngineResult(
        research=_research_result(),
        report=_report(),
        summary=_summary(),
        metadata=_metadata(),
        benchmark_name="SPY",
        experiment_name="adaptive-test",
    )

    assert result.benchmark_name == "SPY"

    assert result.experiment_name == "adaptive-test"
