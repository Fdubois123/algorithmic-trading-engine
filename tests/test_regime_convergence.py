import numpy as np
import pandas as pd
import pytest

from trading_engine.regime.convergence import (
    AdaptiveConvergenceResult,
    run_adaptive_convergence,
)
from trading_engine.regime.labels import (
    MarketRegime,
)


def _returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trend": [
                0.01,
                0.02,
                -0.01,
                0.03,
                0.01,
            ],
            "momentum": [
                0.02,
                0.01,
                -0.02,
                0.04,
                0.01,
            ],
            "mean_reversion": [
                -0.01,
                0.01,
                0.02,
                -0.01,
                0.02,
            ],
            "volatility": [
                0.00,
                -0.01,
                0.03,
                0.01,
                -0.01,
            ],
            "stat_arb": [
                0.01,
                0.01,
                0.01,
                0.01,
                0.01,
            ],
        },
        index=pd.date_range(
            "2026-01-01",
            periods=5,
            freq="D",
        ),
    )


def _regimes(
    index: pd.Index,
) -> pd.Series:
    return pd.Series(
        [
            MarketRegime.LOW_VOL_BULL,
            MarketRegime.LOW_VOL_BULL,
            MarketRegime.HIGH_VOL_BEAR,
            MarketRegime.HIGH_VOL_BEAR,
            MarketRegime.NORMAL_VOL_SIDEWAYS,
        ],
        index=index,
        dtype=object,
    )


def test_convergence_returns_result():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert isinstance(
        result,
        AdaptiveConvergenceResult,
    )

    assert result.periods == len(returns)


def test_first_period_has_zero_applied_weights():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert np.allclose(
        result.applied_weights.iloc[0].to_numpy(),
        0.0,
    )

    assert result.returns.iloc[0] == pytest.approx(0.0)


def test_applied_weights_are_shifted_targets():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert np.allclose(
        result.applied_weights.iloc[1].to_numpy(),
        result.target_weights.iloc[0].to_numpy(),
    )

    assert np.allclose(
        result.applied_weights.iloc[2].to_numpy(),
        result.target_weights.iloc[1].to_numpy(),
    )


def test_no_same_period_lookahead():
    returns = _returns()

    regimes = _regimes(returns.index)

    first = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=regimes,
    )

    modified = regimes.copy()

    modified.iloc[-1] = MarketRegime.LOW_VOL_BEAR

    second = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=modified,
    )

    assert first.returns.iloc[-1] == pytest.approx(second.returns.iloc[-1])


def test_gross_return_matches_applied_weights():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    expected = (result.applied_weights * returns).sum(axis=1)

    assert np.allclose(
        result.gross_returns.to_numpy(),
        expected.to_numpy(),
    )


def test_transaction_costs_reduce_returns():
    returns = _returns()

    regimes = _regimes(returns.index)

    without_cost = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=regimes,
        transaction_cost_bps=0.0,
    )

    with_cost = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=regimes,
        transaction_cost_bps=25.0,
    )

    assert with_cost.returns.sum() <= without_cost.returns.sum() + 1e-12

    assert with_cost.transaction_costs.sum() > 0


def test_transaction_cost_formula():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
        transaction_cost_bps=10.0,
    )

    expected = result.turnover * 10.0 / 10_000.0

    assert np.allclose(
        result.transaction_costs.to_numpy(),
        expected.to_numpy(),
    )


def test_equity_curve_is_compounded_net_returns():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
        transaction_cost_bps=5.0,
    )

    expected = (1.0 + result.returns).cumprod()

    assert np.allclose(
        result.equity_curve.to_numpy(),
        expected.to_numpy(),
    )


def test_final_equity_property():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert result.final_equity == pytest.approx(result.equity_curve.iloc[-1])


def test_total_return_property():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert result.total_return == pytest.approx(result.final_equity - 1.0)


def test_default_confidence_is_supported():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
        confidence=None,
    )

    assert len(result.returns) == len(returns)


def test_confidence_sequence_supported():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
        confidence=[
            1.0,
            0.8,
            0.6,
            0.4,
            0.2,
        ],
    )

    assert result.periods == 5


def test_regime_sequence_supported():
    returns = _returns()

    regimes = list(_regimes(returns.index))

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=regimes,
    )

    assert result.periods == 5


def test_strategy_returns_requires_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        run_adaptive_convergence(
            strategy_returns=[],
            regimes=[],
        )


def test_empty_strategy_returns_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        run_adaptive_convergence(
            strategy_returns=pd.DataFrame(),
            regimes=[],
        )


def test_non_numeric_returns_rejected():
    returns = _returns().astype(object)

    returns.iloc[
        0,
        0,
    ] = "bad"

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
        )


def test_non_finite_returns_rejected():
    returns = _returns()

    returns.iloc[
        0,
        0,
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
        )


def test_duplicate_index_rejected():
    returns = _returns()

    returns.index = [
        0,
        0,
        1,
        2,
        3,
    ]

    with pytest.raises(
        ValueError,
        match="unique",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=[MarketRegime.LOW_VOL_BULL] * 5,
        )


def test_regime_length_must_match():
    returns = _returns()

    with pytest.raises(
        ValueError,
        match="length",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=[MarketRegime.LOW_VOL_BULL],
        )


def test_regime_index_must_match():
    returns = _returns()

    regimes = pd.Series(
        [MarketRegime.LOW_VOL_BULL] * len(returns),
        index=pd.RangeIndex(len(returns)),
    )

    with pytest.raises(
        ValueError,
        match="index",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=regimes,
        )


def test_invalid_regime_value_rejected():
    returns = _returns()

    regimes = list(_regimes(returns.index))

    regimes[2] = "bear"

    with pytest.raises(
        TypeError,
        match="MarketRegime",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=regimes,
        )


def test_confidence_length_must_match():
    returns = _returns()

    with pytest.raises(
        ValueError,
        match="length",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            confidence=[
                1.0,
            ],
        )


def test_confidence_index_must_match():
    returns = _returns()

    confidence = pd.Series(
        1.0,
        index=pd.RangeIndex(len(returns)),
    )

    with pytest.raises(
        ValueError,
        match="index",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            confidence=confidence,
        )


@pytest.mark.parametrize(
    "confidence",
    [
        [
            1.0,
            1.0,
            -0.1,
            1.0,
            1.0,
        ],
        [
            1.0,
            1.0,
            1.1,
            1.0,
            1.0,
        ],
    ],
)
def test_invalid_confidence_rejected(
    confidence,
):
    returns = _returns()

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            confidence=confidence,
        )


def test_non_finite_confidence_rejected():
    returns = _returns()

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            confidence=[
                1.0,
                1.0,
                np.inf,
                1.0,
                1.0,
            ],
        )


@pytest.mark.parametrize(
    "cost",
    [
        True,
        "10",
    ],
)
def test_transaction_cost_requires_numeric(
    cost,
):
    returns = _returns()

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            transaction_cost_bps=cost,
        )


def test_negative_transaction_cost_rejected():
    returns = _returns()

    with pytest.raises(
        ValueError,
        match="negative",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            transaction_cost_bps=-1.0,
        )


def test_non_finite_transaction_cost_rejected():
    returns = _returns()

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        run_adaptive_convergence(
            strategy_returns=returns,
            regimes=_regimes(returns.index),
            transaction_cost_bps=np.inf,
        )


def test_missing_allocator_strategies_are_projected():
    returns = _returns().drop(
        columns=[
            "stat_arb",
        ]
    )

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert list(result.target_weights.columns) == list(returns.columns)

    assert "stat_arb" not in (result.target_weights.columns)

    assert np.isfinite(result.target_weights.to_numpy()).all()


def test_custom_strategy_universe_supported():
    returns = pd.DataFrame(
        {
            "trend": [
                0.01,
                0.02,
                0.03,
            ],
            "momentum": [
                0.02,
                0.01,
                0.02,
            ],
        },
        index=pd.date_range(
            "2026-01-01",
            periods=3,
            freq="D",
        ),
    )

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=[
            MarketRegime.LOW_VOL_BULL,
            MarketRegime.NORMAL_VOL_BULL,
            MarketRegime.HIGH_VOL_BEAR,
        ],
        base_weights={
            "trend": 0.5,
            "momentum": 0.5,
        },
        maximum_turnover=1.0,
    )

    assert list(result.applied_weights.columns) == [
        "trend",
        "momentum",
    ]


def test_results_are_deterministic():
    returns = _returns()

    regimes = _regimes(returns.index)

    first = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=regimes,
        transaction_cost_bps=7.5,
    )

    second = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=regimes,
        transaction_cost_bps=7.5,
    )

    assert np.allclose(
        first.returns.to_numpy(),
        second.returns.to_numpy(),
    )

    assert np.allclose(
        first.target_weights.to_numpy(),
        second.target_weights.to_numpy(),
    )


def test_turnover_is_non_negative():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    assert (result.turnover >= 0.0).all()


def test_gross_exposure_matches_weights():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    expected = result.applied_weights.abs().sum(axis=1)

    assert np.allclose(
        result.gross_exposure.to_numpy(),
        expected.to_numpy(),
    )


def test_cash_weight_matches_exposure():
    returns = _returns()

    result = run_adaptive_convergence(
        strategy_returns=returns,
        regimes=_regimes(returns.index),
    )

    expected = (1.0 - result.gross_exposure).clip(lower=0.0)

    assert np.allclose(
        result.cash_weight.to_numpy(),
        expected.to_numpy(),
    )
