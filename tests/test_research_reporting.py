import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    ResearchReport,
    ResearchResult,
    build_research_report,
)


def research_result():
    index = pd.date_range(
        "2026-01-01",
        periods=30,
        freq="D",
    )

    returns = pd.Series(
        np.sin(np.arange(30) / 3.0) * 0.01,
        index=index,
    )

    equity = (1.0 + returns).cumprod()

    weights = pd.DataFrame(
        {
            "trend": [0.5] * 30,
            "momentum": [0.5] * 30,
        },
        index=index,
    )

    regimes = ["bull" if index_value < 15 else "bear" for index_value in range(30)]

    return ResearchResult(
        equity_curve=equity,
        returns=returns,
        gross_returns=returns,
        regime_frame=pd.DataFrame(
            {
                "market_regime": regimes,
            },
            index=index,
        ),
        target_weights=weights.copy(),
        applied_weights=weights,
        turnover=pd.Series(
            [0.0] + [0.05] * 29,
            index=index,
        ),
        transaction_costs=pd.Series(
            [0.0] + [0.0001] * 29,
            index=index,
        ),
    )


def strategy_returns():
    index = research_result().returns.index

    return pd.DataFrame(
        {
            "trend": (np.sin(np.arange(30) / 4.0) * 0.01),
            "momentum": (np.cos(np.arange(30) / 5.0) * 0.01),
        },
        index=index,
    )


def test_build_research_report():
    result = build_research_report(
        result=research_result(),
        strategy_returns=strategy_returns(),
        rolling_window=5,
    )

    assert isinstance(
        result,
        ResearchReport,
    )


def test_report_overview():
    report = build_research_report(
        result=research_result(),
        strategy_returns=strategy_returns(),
        rolling_window=5,
    )

    assert {
        "observations",
        "final_equity",
        "total_return",
        "maximum_drawdown",
        "maximum_drawdown_duration",
        "total_transaction_cost",
        "average_turnover",
    } == set(report.overview.index)


def test_report_contains_rolling_metrics():
    report = build_research_report(
        result=research_result(),
        strategy_returns=strategy_returns(),
        rolling_window=5,
    )

    assert list(report.rolling_metrics.columns) == [
        "rolling_volatility",
        "rolling_sharpe",
    ]

    assert len(report.rolling_metrics) == 30


def test_report_contains_rankings():
    report = build_research_report(
        result=research_result(),
        strategy_returns=strategy_returns(),
        rolling_window=5,
    )

    assert not report.strategy_ranking.empty
    assert not report.regime_ranking.empty


def test_report_requires_research_result():
    with pytest.raises(
        TypeError,
        match="ResearchResult",
    ):
        build_research_report(
            result="bad",
            strategy_returns=strategy_returns(),
        )


def test_report_requires_strategy_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        build_research_report(
            result=research_result(),
            strategy_returns=[],
        )


def test_report_index_must_match():
    altered = strategy_returns().reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="index",
    ):
        build_research_report(
            result=research_result(),
            strategy_returns=altered,
        )


def test_report_columns_must_match():
    altered = strategy_returns().rename(
        columns={
            "trend": "other",
        }
    )

    with pytest.raises(
        ValueError,
        match="columns",
    ):
        build_research_report(
            result=research_result(),
            strategy_returns=altered,
        )
