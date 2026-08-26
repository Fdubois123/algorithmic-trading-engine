import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    ResearchConfig,
    rolling_sharpe_ratio,
)
from trading_engine.research.diagnostics import (
    cost_diagnostics,
)
from trading_engine.research.result import (
    ResearchResult,
)
from trading_engine.research.runner import (
    _extract_regimes,
    _validate_strategy_returns,
)


def test_result_empty_equity_defaults_to_one():
    result = ResearchResult(
        equity_curve=pd.Series(dtype=float),
        returns=pd.Series(dtype=float),
        gross_returns=pd.Series(dtype=float),
        regime_frame=pd.DataFrame(),
        target_weights=pd.DataFrame(),
        applied_weights=pd.DataFrame(),
        turnover=pd.Series(dtype=float),
        transaction_costs=pd.Series(dtype=float),
    )

    assert result.final_equity == 1.0
    assert result.total_return == 0.0
    assert result.average_turnover == 0.0


@pytest.mark.parametrize(
    "field",
    [
        "trend_threshold",
        "momentum_threshold",
        "minimum_exposure",
        "maximum_turnover",
        "transaction_cost_bps",
    ],
)
def test_research_config_non_finite_numeric_fields(
    field,
):
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        ResearchConfig(
            **{
                field: np.inf,
            }
        )


def test_strategy_returns_empty_rejected_directly():
    index = pd.RangeIndex(2)

    with pytest.raises(
        ValueError,
        match="empty",
    ):
        _validate_strategy_returns(
            pd.DataFrame(index=index),
            index=index,
        )


def test_strategy_returns_non_numeric_rejected_directly():
    index = pd.RangeIndex(2)

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        _validate_strategy_returns(
            pd.DataFrame(
                {
                    "trend": [
                        "a",
                        "b",
                    ]
                },
                index=index,
            ),
            index=index,
        )


def test_extract_regimes_requires_valid_observation():
    frame = pd.DataFrame(
        {
            "market_regime": [
                pd.NA,
                pd.NA,
            ],
            "regime_confidence": [
                np.nan,
                np.nan,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="no valid observations",
    ):
        _extract_regimes(frame)


def test_extract_regimes_fills_warmup_values():
    frame = pd.DataFrame(
        {
            "market_regime": [
                pd.NA,
                "normal_vol_bull",
            ],
            "regime_confidence": [
                np.nan,
                0.75,
            ],
        }
    )

    regimes, confidence = _extract_regimes(frame)

    assert regimes.iloc[0].value == ("normal_vol_sideways")

    assert confidence.iloc[0] == 0.0


def test_cost_diagnostics_negative_turnover_rejected():
    index = pd.RangeIndex(2)

    with pytest.raises(
        ValueError,
        match="turnover cannot be negative",
    ):
        cost_diagnostics(
            transaction_costs=pd.Series(
                [
                    0.0,
                    0.0,
                ],
                index=index,
            ),
            turnover=pd.Series(
                [
                    0.0,
                    -0.1,
                ],
                index=index,
            ),
            gross_returns=pd.Series(
                [
                    0.01,
                    0.01,
                ],
                index=index,
            ),
        )


@pytest.mark.parametrize(
    "periods",
    [
        True,
        252.5,
        "252",
    ],
)
def test_sharpe_periods_per_year_requires_integer(
    periods,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_sharpe_ratio(
            pd.Series(
                [
                    0.01,
                    0.02,
                ]
            ),
            window=2,
            periods_per_year=periods,
        )


def test_sharpe_periods_per_year_positive():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        rolling_sharpe_ratio(
            pd.Series(
                [
                    0.01,
                    0.02,
                ]
            ),
            window=2,
            periods_per_year=0,
        )


def test_sharpe_risk_free_requires_numeric():
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        rolling_sharpe_ratio(
            pd.Series(
                [
                    0.01,
                    0.02,
                ]
            ),
            window=2,
            risk_free_rate="0.1",
        )


def test_sharpe_non_finite_risk_free_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        rolling_sharpe_ratio(
            pd.Series(
                [
                    0.01,
                    0.02,
                ]
            ),
            window=2,
            risk_free_rate=np.inf,
        )
