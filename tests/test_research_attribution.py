import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    StrategyAttribution,
    contribution_totals,
    strategy_attribution,
    strategy_contribution_frame,
)


def strategy_returns():
    return pd.DataFrame(
        {
            "trend": [
                0.01,
                0.02,
                -0.01,
            ],
            "momentum": [
                0.02,
                -0.01,
                0.03,
            ],
        },
        index=pd.date_range(
            "2026-01-01",
            periods=3,
            freq="D",
        ),
    )


def weights():
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
        },
        index=strategy_returns().index,
    )


def test_strategy_contribution_frame():
    result = strategy_contribution_frame(
        strategy_returns(),
        weights(),
    )

    assert result.iloc[0]["trend"] == pytest.approx(0.005)


def test_strategy_attribution():
    result = strategy_attribution(
        strategy_returns(),
        weights(),
    )

    assert len(result) == 2

    assert isinstance(
        result[0],
        StrategyAttribution,
    )


def test_contribution_totals():
    result = contribution_totals(
        strategy_returns(),
        weights(),
    )

    assert set(result.index) == {
        "trend",
        "momentum",
    }


def test_strategy_returns_requires_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        strategy_contribution_frame(
            [],
            weights(),
        )


def test_weights_requires_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        strategy_contribution_frame(
            strategy_returns(),
            [],
        )


def test_empty_strategy_returns_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        strategy_contribution_frame(
            pd.DataFrame(),
            pd.DataFrame(),
        )


def test_indexes_must_match():
    altered = weights().reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="indexes",
    ):
        strategy_contribution_frame(
            strategy_returns(),
            altered,
        )


def test_columns_must_match():
    altered = weights().rename(
        columns={
            "trend": "other",
        }
    )

    with pytest.raises(
        ValueError,
        match="columns",
    ):
        strategy_contribution_frame(
            strategy_returns(),
            altered,
        )


def test_non_finite_returns_rejected():
    values = strategy_returns()

    values.iloc[
        0,
        0,
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        strategy_contribution_frame(
            values,
            weights(),
        )


def test_non_finite_weights_rejected():
    values = weights()

    values.iloc[
        0,
        0,
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        strategy_contribution_frame(
            strategy_returns(),
            values,
        )
