import pandas as pd
import pytest

from trading_engine.research import (
    BenchmarkComparison,
    ExperimentSummary,
    ResearchResult,
    build_experiment_summary,
)


def research_result():
    index = pd.date_range(
        "2026-01-01",
        periods=4,
        freq="D",
    )

    returns = pd.Series(
        [
            0.0,
            0.01,
            -0.01,
            0.02,
        ],
        index=index,
    )

    applied_weights = pd.DataFrame(
        {
            "trend": [
                0.0,
                0.5,
                0.5,
                0.5,
            ],
            "momentum": [
                0.0,
                0.5,
                0.5,
                0.5,
            ],
        },
        index=index,
    )

    return ResearchResult(
        equity_curve=(1.0 + returns).cumprod(),
        returns=returns,
        gross_returns=returns,
        regime_frame=pd.DataFrame(
            {
                "market_regime": [
                    "bull",
                    "bull",
                    "bear",
                    "bear",
                ]
            },
            index=index,
        ),
        target_weights=applied_weights.copy(),
        applied_weights=applied_weights,
        turnover=pd.Series(
            [
                0.0,
                0.5,
                0.0,
                0.0,
            ],
            index=index,
        ),
        transaction_costs=pd.Series(
            [
                0.0,
                0.001,
                0.0,
                0.0,
            ],
            index=index,
        ),
    )


def strategy_returns():
    index = research_result().returns.index

    return pd.DataFrame(
        {
            "trend": [
                0.01,
                0.02,
                -0.01,
                0.03,
            ],
            "momentum": [
                0.02,
                0.00,
                -0.01,
                0.01,
            ],
        },
        index=index,
    )


def benchmark_returns():
    return pd.Series(
        [
            0.0,
            0.005,
            -0.005,
            0.01,
        ],
        index=research_result().returns.index,
    )


def test_build_summary_without_benchmark():
    result = build_experiment_summary(
        result=research_result(),
        strategy_returns=strategy_returns(),
    )

    assert isinstance(
        result,
        ExperimentSummary,
    )

    assert result.benchmark is None


def test_build_summary_with_benchmark():
    result = build_experiment_summary(
        result=research_result(),
        strategy_returns=strategy_returns(),
        benchmark_returns=benchmark_returns(),
    )

    assert isinstance(
        result.benchmark,
        BenchmarkComparison,
    )


def test_summary_contains_strategy_contributions():
    result = build_experiment_summary(
        result=research_result(),
        strategy_returns=strategy_returns(),
    )

    assert set(result.strategy_contributions.index) == {
        "trend",
        "momentum",
    }


def test_summary_contains_regime_performance():
    result = build_experiment_summary(
        result=research_result(),
        strategy_returns=strategy_returns(),
    )

    assert not result.regime_performance.empty


def test_summary_requires_research_result():
    with pytest.raises(
        TypeError,
        match="ResearchResult",
    ):
        build_experiment_summary(
            result="bad",
            strategy_returns=strategy_returns(),
        )


def test_summary_requires_strategy_returns_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        build_experiment_summary(
            result=research_result(),
            strategy_returns=[],
        )


def test_strategy_return_index_must_match():
    altered = strategy_returns().reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="index",
    ):
        build_experiment_summary(
            result=research_result(),
            strategy_returns=altered,
        )
