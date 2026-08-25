import numpy as np
import pandas as pd
import pytest

from trading_engine.indicators.returns import (
    cumulative_returns,
    log_returns,
    simple_returns,
    wealth_index,
)


@pytest.fixture
def prices():
    return pd.Series(
        [100.0, 110.0, 121.0],
        index=pd.date_range("2026-01-01", periods=3),
        name="close",
    )


def test_simple_returns_are_mathematically_correct(prices):
    result = simple_returns(prices)

    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(0.10)
    assert result.iloc[2] == pytest.approx(0.10)


def test_log_returns_are_mathematically_correct(prices):
    result = log_returns(prices)

    expected = np.log(1.10)

    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(expected)
    assert result.iloc[2] == pytest.approx(expected)


def test_simple_returns_preserve_index(prices):
    result = simple_returns(prices)

    pd.testing.assert_index_equal(result.index, prices.index)


def test_log_returns_preserve_index(prices):
    result = log_returns(prices)

    pd.testing.assert_index_equal(result.index, prices.index)


def test_simple_returns_have_expected_name(prices):
    result = simple_returns(prices)

    assert result.name == "simple_return"


def test_cumulative_returns_are_correct():
    returns = pd.Series([0.10, -0.05, 0.20])

    result = cumulative_returns(returns)

    expected = pd.Series(
        [
            0.10,
            (1.10 * 0.95) - 1,
            (1.10 * 0.95 * 1.20) - 1,
        ],
        name="cumulative_return",
    )

    pd.testing.assert_series_equal(result, expected)


def test_wealth_index_is_correct():
    returns = pd.Series([0.10, -0.05])

    result = wealth_index(
        returns,
        initial_capital=100_000,
    )

    assert result.iloc[0] == pytest.approx(110_000)
    assert result.iloc[1] == pytest.approx(104_500)


@pytest.mark.parametrize(
    "prices",
    [
        pd.Series([100.0, 0.0, 105.0]),
        pd.Series([100.0, -5.0, 105.0]),
    ],
)
def test_non_positive_prices_raise_error(prices):
    with pytest.raises(ValueError, match="strictly positive"):
        simple_returns(prices)


def test_nan_price_raises_error():
    prices = pd.Series([100.0, np.nan, 105.0])

    with pytest.raises(ValueError, match="missing"):
        simple_returns(prices)


def test_infinite_price_raises_error():
    prices = pd.Series([100.0, np.inf, 105.0])

    with pytest.raises(ValueError, match="finite"):
        simple_returns(prices)


def test_empty_prices_raise_error():
    with pytest.raises(ValueError, match="empty"):
        simple_returns(pd.Series(dtype=float))


def test_non_series_prices_raise_error():
    with pytest.raises(TypeError, match="pandas Series"):
        simple_returns([100.0, 101.0])


def test_return_below_negative_one_raises_error():
    returns = pd.Series([0.10, -1.20])

    with pytest.raises(ValueError, match="-100%"):
        cumulative_returns(returns)


def test_zero_initial_capital_raises_error():
    returns = pd.Series([0.01, 0.02])

    with pytest.raises(ValueError, match="greater than zero"):
        wealth_index(returns, initial_capital=0)
