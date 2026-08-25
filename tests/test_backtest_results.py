import pandas as pd
import pytest

from trading_engine.backtest.results import (
    BacktestResult,
)


def test_total_return():
    equity = pd.Series([100.0, 110.0, 121.0])

    result = BacktestResult(
        equity_curve=equity,
        fills=(),
        periods_per_year=1,
    )

    assert result.total_return == pytest.approx(0.21)


def test_returns_generated():
    equity = pd.Series([100.0, 110.0, 121.0])

    result = BacktestResult(
        equity_curve=equity,
        fills=(),
    )

    returns = result.returns

    assert returns.iloc[1] > 0


def test_metrics_are_generated():
    equity = pd.Series(
        [
            100.0,
            101.0,
            100.5,
            103.0,
            104.0,
        ]
    )

    result = BacktestResult(
        equity_curve=equity,
        fills=(),
        periods_per_year=252,
    )

    metrics = result.metrics()

    assert "sharpe_ratio" in metrics
    assert "max_drawdown" in metrics
    assert "total_return" in metrics


def test_empty_equity_curve_has_zero_total_return():
    result = BacktestResult(
        equity_curve=pd.Series(dtype=float),
        fills=(),
    )

    assert result.total_return == pytest.approx(0.0)


def test_single_equity_observation_returns_minimal_metrics():
    equity = pd.Series([100.0])

    result = BacktestResult(
        equity_curve=equity,
        fills=(),
    )

    metrics = result.metrics()

    assert metrics["total_return"] == pytest.approx(0.0)
    assert metrics["max_drawdown"] == pytest.approx(0.0)
    assert "sharpe_ratio" not in metrics


def test_maximum_drawdown_property():
    equity = pd.Series([100.0, 120.0, 90.0, 110.0])

    result = BacktestResult(
        equity_curve=equity,
        fills=(),
    )

    assert result.maximum_drawdown == pytest.approx(-0.25)


def test_returns_series_has_expected_name():
    result = BacktestResult(
        equity_curve=pd.Series([100.0, 101.0]),
        fills=(),
    )

    assert result.returns.name == "returns"
