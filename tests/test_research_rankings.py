import pandas as pd
import pytest

from trading_engine.research import (
    RegimeRanking,
    StrategyRanking,
    rank_regimes,
    rank_strategies,
    regime_ranking_table,
    strategy_ranking_table,
)


def strategy_returns():
    return pd.DataFrame(
        {
            "trend": [
                0.02,
                0.02,
                0.02,
            ],
            "momentum": [
                -0.01,
                0.00,
                0.01,
            ],
        }
    )


def applied_weights():
    return pd.DataFrame(
        {
            "trend": [
                0.5,
                0.5,
                0.5,
            ],
            "momentum": [
                0.5,
                0.5,
                0.5,
            ],
        }
    )


def test_rank_strategies():
    result = rank_strategies(
        strategy_returns(),
        applied_weights(),
    )

    assert isinstance(
        result[0],
        StrategyRanking,
    )

    assert result[0].rank == 1
    assert result[0].strategy == "trend"


def test_strategy_ranking_table():
    result = strategy_ranking_table(
        strategy_returns(),
        applied_weights(),
    )

    assert list(result.columns) == [
        "rank",
        "strategy",
        "contribution",
    ]


def test_rank_regimes():
    returns = pd.Series(
        [
            0.02,
            0.02,
            -0.02,
            -0.01,
        ]
    )

    regimes = pd.Series(
        [
            "bull",
            "bull",
            "bear",
            "bear",
        ]
    )

    result = rank_regimes(
        returns,
        regimes,
    )

    assert isinstance(
        result[0],
        RegimeRanking,
    )

    assert result[0].regime == "bull"


def test_regime_ranking_table():
    returns = pd.Series(
        [
            0.02,
            -0.01,
        ]
    )

    regimes = pd.Series(
        [
            "bull",
            "bear",
        ]
    )

    result = regime_ranking_table(
        returns,
        regimes,
    )

    assert {
        "rank",
        "regime",
        "cumulative_return",
        "average_return",
        "observations",
    } == set(result.columns)


def test_strategy_rankings_are_descending():
    result = rank_strategies(
        strategy_returns(),
        applied_weights(),
    )

    values = [item.contribution for item in result]

    assert values == sorted(
        values,
        reverse=True,
    )


def test_regime_rankings_are_descending():
    returns = pd.Series(
        [
            0.05,
            0.02,
            -0.04,
            -0.02,
        ]
    )

    regimes = pd.Series(
        [
            "bull",
            "bull",
            "bear",
            "bear",
        ]
    )

    result = rank_regimes(
        returns,
        regimes,
    )

    values = [item.cumulative_return for item in result]

    assert values == sorted(
        values,
        reverse=True,
    )


def test_rank_strategy_validation_propagates():
    with pytest.raises(
        ValueError,
        match="columns",
    ):
        rank_strategies(
            strategy_returns(),
            applied_weights().rename(
                columns={
                    "trend": "other",
                }
            ),
        )
