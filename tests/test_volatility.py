import numpy as np
import pandas as pd
import pytest

from trading_engine.indicators.volatility import (
    annualized_volatility,
    close_to_close_volatility,
    downside_volatility,
    ewma_volatility,
    historical_volatility,
    parkinson_volatility,
)


@pytest.fixture
def returns():
    return pd.Series(
        [0.01, -0.02, 0.03, -0.01, 0.02],
        index=pd.date_range("2026-01-01", periods=5),
    )


def test_historical_volatility_matches_pandas(returns):
    result = historical_volatility(
        returns,
        window=3,
    )

    expected = returns.rolling(3).std(ddof=1)
    expected.name = "historical_volatility"

    pd.testing.assert_series_equal(result, expected)


def test_historical_volatility_preserves_index(returns):
    result = historical_volatility(
        returns,
        window=3,
    )

    pd.testing.assert_index_equal(result.index, returns.index)


def test_historical_volatility_has_expected_name(returns):
    result = historical_volatility(
        returns,
        window=3,
    )

    assert result.name == "historical_volatility"


def test_annualized_volatility_is_correct(returns):
    result = annualized_volatility(
        returns,
        window=3,
        periods_per_year=252,
    )

    base = returns.rolling(3).std(ddof=1)
    expected = base * np.sqrt(252)

    assert result.iloc[-1] == pytest.approx(expected.iloc[-1])


def test_annualized_volatility_respects_custom_periods(returns):
    result = annualized_volatility(
        returns,
        window=3,
        periods_per_year=12,
    )

    base = returns.rolling(3).std(ddof=1)

    assert result.iloc[-1] == pytest.approx(base.iloc[-1] * np.sqrt(12))


@pytest.mark.parametrize("periods", [0, -1])
def test_invalid_periods_per_year_raise_error(returns, periods):
    with pytest.raises(ValueError, match="greater than zero"):
        annualized_volatility(
            returns,
            window=3,
            periods_per_year=periods,
        )


def test_downside_volatility_is_correct():
    returns = pd.Series([-0.02, 0.01, -0.04])

    result = downside_volatility(
        returns,
        window=3,
    )

    expected = np.sqrt(((-0.02) ** 2 + 0.0**2 + (-0.04) ** 2) / 3)

    assert result.iloc[-1] == pytest.approx(expected)


def test_downside_volatility_is_zero_without_downside():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = downside_volatility(
        returns,
        window=3,
    )

    assert result.iloc[-1] == pytest.approx(0.0)


def test_downside_volatility_respects_target():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = downside_volatility(
        returns,
        window=3,
        target_return=0.02,
    )

    expected = np.sqrt(((-0.01) ** 2 + 0.0**2 + 0.0**2) / 3)

    assert result.iloc[-1] == pytest.approx(expected)


def test_downside_volatility_can_be_annualized():
    returns = pd.Series([-0.01, -0.02, 0.01])

    result = downside_volatility(
        returns,
        window=3,
        periods_per_year=252,
    )

    base = downside_volatility(
        returns,
        window=3,
    )

    assert result.iloc[-1] == pytest.approx(base.iloc[-1] * np.sqrt(252))


def test_invalid_target_return_type_raises_error(returns):
    with pytest.raises(TypeError, match="numeric"):
        downside_volatility(
            returns,
            window=3,
            target_return="0",
        )


def test_ewma_volatility_matches_pandas(returns):
    result = ewma_volatility(
        returns,
        span=3,
    )

    expected = returns.ewm(
        span=3,
        adjust=False,
        min_periods=1,
    ).std(bias=False)

    expected.name = "ewma_volatility"

    pd.testing.assert_series_equal(result, expected)


def test_ewma_volatility_preserves_index(returns):
    result = ewma_volatility(
        returns,
        span=3,
    )

    pd.testing.assert_index_equal(result.index, returns.index)


def test_ewma_volatility_can_be_annualized(returns):
    result = ewma_volatility(
        returns,
        span=3,
        periods_per_year=252,
    )

    base = ewma_volatility(
        returns,
        span=3,
    )

    pd.testing.assert_series_equal(
        result,
        base * np.sqrt(252),
        check_names=False,
    )


@pytest.mark.parametrize("span", [0, -1])
def test_invalid_ewma_span_raises_error(returns, span):
    with pytest.raises(ValueError, match="greater than zero"):
        ewma_volatility(
            returns,
            span=span,
        )


def test_parkinson_volatility_is_correct():
    high = pd.Series([110.0, 112.0, 115.0])
    low = pd.Series([100.0, 101.0, 103.0])

    result = parkinson_volatility(
        high,
        low,
        window=3,
    )

    log_ranges = np.log(high / low) ** 2
    expected = np.sqrt(log_ranges.mean() / (4.0 * np.log(2.0)))

    assert result.iloc[-1] == pytest.approx(expected)


def test_parkinson_preserves_index():
    index = pd.date_range("2026-01-01", periods=3)

    high = pd.Series([110.0, 111.0, 112.0], index=index)
    low = pd.Series([100.0, 101.0, 102.0], index=index)

    result = parkinson_volatility(
        high,
        low,
        window=3,
    )

    pd.testing.assert_index_equal(result.index, index)


def test_parkinson_rejects_high_below_low():
    high = pd.Series([100.0, 90.0, 110.0])
    low = pd.Series([95.0, 95.0, 100.0])

    with pytest.raises(ValueError, match="cannot be lower"):
        parkinson_volatility(
            high,
            low,
            window=3,
        )


def test_parkinson_rejects_mismatched_indices():
    high = pd.Series(
        [110.0, 111.0, 112.0],
        index=pd.date_range("2026-01-01", periods=3),
    )

    low = pd.Series(
        [100.0, 101.0, 102.0],
        index=pd.date_range("2026-01-02", periods=3),
    )

    with pytest.raises(ValueError, match="indices must match"):
        parkinson_volatility(
            high,
            low,
            window=3,
        )


def test_parkinson_constant_prices_have_zero_volatility():
    high = pd.Series([100.0, 100.0, 100.0])
    low = pd.Series([100.0, 100.0, 100.0])

    result = parkinson_volatility(
        high,
        low,
        window=3,
    )

    assert result.iloc[-1] == pytest.approx(0.0)


def test_close_to_close_matches_log_return_volatility():
    prices = pd.Series([100.0, 102.0, 101.0, 104.0])

    result = close_to_close_volatility(
        prices,
        window=3,
    )

    returns = np.log(prices / prices.shift(1))
    expected = returns.rolling(3).std(ddof=1)

    assert result.iloc[-1] == pytest.approx(expected.iloc[-1])


def test_close_to_close_preserves_index():
    index = pd.date_range("2026-01-01", periods=4)
    prices = pd.Series([100.0, 101.0, 103.0, 102.0], index=index)

    result = close_to_close_volatility(
        prices,
        window=3,
    )

    pd.testing.assert_index_equal(result.index, index)


def test_close_to_close_rejects_non_positive_prices():
    prices = pd.Series([100.0, 0.0, 102.0])

    with pytest.raises(ValueError, match="strictly positive"):
        close_to_close_volatility(
            prices,
            window=3,
        )
