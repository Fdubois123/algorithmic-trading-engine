import pandas as pd
import pytest

from trading_engine.research import (
    ResearchResult,
)


def result() -> ResearchResult:
    index = pd.date_range(
        "2026-01-01",
        periods=3,
        freq="D",
    )

    returns = pd.Series(
        [
            0.0,
            0.01,
            0.02,
        ],
        index=index,
    )

    equity = (1.0 + returns).cumprod()

    return ResearchResult(
        equity_curve=equity,
        returns=returns,
        gross_returns=returns,
        regime_frame=pd.DataFrame(index=index),
        target_weights=pd.DataFrame(index=index),
        applied_weights=pd.DataFrame(index=index),
        turnover=pd.Series(
            [
                0.0,
                0.1,
                0.2,
            ],
            index=index,
        ),
        transaction_costs=pd.Series(
            [
                0.0,
                0.001,
                0.002,
            ],
            index=index,
        ),
    )


def test_result_observations():
    assert result().observations == 3


def test_final_equity():
    value = result()

    assert value.final_equity == pytest.approx(value.equity_curve.iloc[-1])


def test_total_return():
    value = result()

    assert value.total_return == pytest.approx(value.final_equity - 1.0)


def test_total_transaction_cost():
    assert result().total_transaction_cost == pytest.approx(0.003)


def test_average_turnover():
    assert result().average_turnover == pytest.approx(0.1)
