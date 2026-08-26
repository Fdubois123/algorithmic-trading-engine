import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    CostDiagnostics,
    DrawdownDiagnostics,
    cost_diagnostics,
    drawdown_duration,
    equity_drawdown,
    rolling_annualized_volatility,
    rolling_sharpe_ratio,
    summarize_drawdown,
)


def series(values):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def test_equity_drawdown():
    result = equity_drawdown(
        series(
            [
                1.0,
                1.1,
                0.99,
            ]
        )
    )

    assert result.iloc[0] == pytest.approx(0.0)

    assert result.iloc[1] == pytest.approx(0.0)

    assert result.iloc[2] == pytest.approx(-0.1)


def test_drawdown_duration():
    result = drawdown_duration(
        series(
            [
                1.0,
                0.9,
                0.8,
                1.1,
                1.0,
            ]
        )
    )

    assert result.tolist() == [
        0,
        1,
        2,
        0,
        1,
    ]


def test_summarize_drawdown():
    result = summarize_drawdown(
        series(
            [
                1.0,
                1.2,
                0.9,
                1.0,
            ]
        )
    )

    assert isinstance(
        result,
        DrawdownDiagnostics,
    )

    assert result.maximum_drawdown < 0
    assert result.maximum_drawdown_duration > 0


def test_non_positive_equity_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        equity_drawdown(
            series(
                [
                    1.0,
                    0.0,
                ]
            )
        )


def test_rolling_volatility():
    result = rolling_annualized_volatility(
        series(
            [
                0.01,
                -0.01,
                0.02,
                -0.02,
            ]
        ),
        window=2,
    )

    assert result.iloc[0] != result.iloc[0]
    assert result.iloc[-1] > 0


def test_rolling_sharpe():
    result = rolling_sharpe_ratio(
        series(
            [
                0.01,
                -0.01,
                0.02,
                0.01,
            ]
        ),
        window=2,
    )

    assert len(result) == 4


def test_zero_volatility_sharpe_is_nan():
    result = rolling_sharpe_ratio(
        series(
            [
                0.01,
                0.01,
                0.01,
            ]
        ),
        window=2,
    )

    assert result.iloc[1:].isna().all()


@pytest.mark.parametrize(
    "window",
    [
        True,
        1.5,
        "20",
    ],
)
def test_rolling_window_requires_integer(
    window,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_annualized_volatility(
            series(
                [
                    0.01,
                    0.02,
                ]
            ),
            window=window,
        )


def test_rolling_window_requires_two():
    with pytest.raises(
        ValueError,
        match="at least 2",
    ):
        rolling_sharpe_ratio(
            series(
                [
                    0.01,
                    0.02,
                ]
            ),
            window=1,
        )


def test_cost_diagnostics():
    result = cost_diagnostics(
        transaction_costs=series(
            [
                0.0,
                0.001,
                0.002,
            ]
        ),
        turnover=series(
            [
                0.0,
                0.2,
                0.3,
            ]
        ),
        gross_returns=series(
            [
                0.01,
                0.02,
                0.01,
            ]
        ),
    )

    assert isinstance(
        result,
        CostDiagnostics,
    )

    assert result.total_cost == pytest.approx(0.003)

    assert result.total_turnover == pytest.approx(0.5)


def test_zero_gross_return_cost_ratio():
    result = cost_diagnostics(
        transaction_costs=series(
            [
                0.001,
                0.001,
            ]
        ),
        turnover=series(
            [
                0.1,
                0.1,
            ]
        ),
        gross_returns=series(
            [
                0.01,
                -0.01,
            ]
        ),
    )

    assert result.cost_to_gross_return_ratio == 0.0


def test_cost_indexes_must_match():
    costs = series(
        [
            0.0,
            0.001,
        ]
    )

    turnover = pd.Series(
        [
            0.0,
            0.1,
        ]
    )

    with pytest.raises(
        ValueError,
        match="matching indexes",
    ):
        cost_diagnostics(
            transaction_costs=costs,
            turnover=turnover,
            gross_returns=costs,
        )


def test_negative_cost_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        cost_diagnostics(
            transaction_costs=series(
                [
                    0.0,
                    -0.001,
                ]
            ),
            turnover=series(
                [
                    0.0,
                    0.1,
                ]
            ),
            gross_returns=series(
                [
                    0.01,
                    0.01,
                ]
            ),
        )


def test_non_finite_series_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        equity_drawdown(
            series(
                [
                    1.0,
                    np.inf,
                ]
            )
        )
