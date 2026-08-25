import pandas as pd
import pytest

from trading_engine.performance.drawdown import (
    drawdown_duration,
    drawdown_series,
    max_drawdown,
    underwater_curve,
)


def test_drawdown_series_is_correct():
    wealth = pd.Series([100.0, 110.0, 99.0, 121.0])

    result = drawdown_series(wealth)

    assert result.iloc[0] == pytest.approx(0.0)
    assert result.iloc[1] == pytest.approx(0.0)
    assert result.iloc[2] == pytest.approx(-0.10)
    assert result.iloc[3] == pytest.approx(0.0)


def test_max_drawdown_is_correct():
    wealth = pd.Series([100.0, 120.0, 90.0, 110.0])

    result = max_drawdown(wealth)

    assert result == pytest.approx(-0.25)


def test_monotonically_increasing_wealth_has_zero_drawdown():
    wealth = pd.Series([100.0, 110.0, 120.0])

    assert max_drawdown(wealth) == pytest.approx(0.0)


def test_underwater_curve_is_positive():
    wealth = pd.Series([100.0, 120.0, 90.0])

    result = underwater_curve(wealth)

    assert result.iloc[-1] == pytest.approx(0.25)


def test_drawdown_preserves_index():
    index = pd.date_range("2026-01-01", periods=3)
    wealth = pd.Series([100.0, 90.0, 110.0], index=index)

    result = drawdown_series(wealth)

    pd.testing.assert_index_equal(result.index, index)


def test_drawdown_duration_is_correct():
    wealth = pd.Series([100.0, 90.0, 80.0, 110.0, 100.0, 120.0])

    result = drawdown_duration(wealth)

    assert result.tolist() == [0, 1, 2, 0, 1, 0]


@pytest.mark.parametrize(
    "values",
    [
        [100.0, 0.0, 90.0],
        [100.0, -10.0, 90.0],
    ],
)
def test_drawdown_rejects_non_positive_wealth(values):
    with pytest.raises(ValueError, match="strictly positive"):
        drawdown_series(pd.Series(values))
