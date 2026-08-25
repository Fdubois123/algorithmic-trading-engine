import numpy as np
import pandas as pd
import pytest

from trading_engine.performance.metrics import (
    annualized_return,
    cagr,
    calmar_ratio,
    information_ratio,
    sharpe_ratio,
    sortino_ratio,
    tracking_error,
)


def test_cagr_is_correct():
    result = cagr(
        initial_value=100.0,
        final_value=121.0,
        years=2.0,
    )

    assert result == pytest.approx(0.10)


def test_annualized_return_is_correct():
    returns = pd.Series([0.10, 0.10])

    result = annualized_return(
        returns,
        periods_per_year=1,
    )

    expected = (1.10 * 1.10) ** (1 / 2) - 1

    assert result == pytest.approx(expected)


def test_sharpe_ratio_is_correct():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = sharpe_ratio(
        returns,
        periods_per_year=1,
    )

    expected = returns.mean() / returns.std(ddof=1)

    assert result == pytest.approx(expected)


def test_constant_returns_produce_nan_sharpe():
    returns = pd.Series([0.01, 0.01, 0.01])

    result = sharpe_ratio(
        returns,
        periods_per_year=252,
    )

    assert np.isnan(result)


def test_sortino_ratio_is_correct():
    returns = pd.Series([-0.02, 0.01, -0.01])

    result = sortino_ratio(
        returns,
        periods_per_year=1,
    )

    downside = np.minimum(returns, 0.0)
    expected = returns.mean() / np.sqrt(np.mean(downside**2))

    assert result == pytest.approx(expected)


def test_no_downside_produces_nan_sortino():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = sortino_ratio(returns)

    assert np.isnan(result)


def test_calmar_ratio_is_correct():
    returns = pd.Series([0.10, -0.20, 0.10])

    result = calmar_ratio(
        returns,
        periods_per_year=1,
    )

    assert np.isfinite(result)


def test_tracking_error_is_correct():
    portfolio = pd.Series([0.02, 0.01, 0.03])
    benchmark = pd.Series([0.01, 0.01, 0.02])

    result = tracking_error(
        portfolio,
        benchmark,
        periods_per_year=1,
    )

    expected = (portfolio - benchmark).std(ddof=1)

    assert result == pytest.approx(expected)


def test_identical_returns_have_zero_tracking_error():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = tracking_error(
        returns,
        returns,
        periods_per_year=1,
    )

    assert result == pytest.approx(0.0)


def test_information_ratio_is_correct():
    portfolio = pd.Series([0.03, 0.02, 0.04])
    benchmark = pd.Series([0.01, 0.01, 0.02])

    result = information_ratio(
        portfolio,
        benchmark,
        periods_per_year=1,
    )

    active = portfolio - benchmark
    expected = active.mean() / active.std(ddof=1)

    assert result == pytest.approx(expected)


def test_zero_tracking_error_produces_nan_information_ratio():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = information_ratio(
        returns,
        returns,
    )

    assert np.isnan(result)


def test_tracking_error_rejects_mismatched_indices():
    portfolio = pd.Series(
        [0.01, 0.02],
        index=pd.date_range("2026-01-01", periods=2),
    )

    benchmark = pd.Series(
        [0.01, 0.02],
        index=pd.date_range("2026-01-02", periods=2),
    )

    with pytest.raises(ValueError, match="indices must match"):
        tracking_error(
            portfolio,
            benchmark,
        )


@pytest.mark.parametrize(
    "years",
    [0, -1],
)
def test_cagr_rejects_invalid_years(years):
    with pytest.raises(ValueError, match="greater than zero"):
        cagr(
            initial_value=100,
            final_value=120,
            years=years,
        )


def test_annualized_return_rejects_empty_valid_observations():
    returns = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        annualized_return(returns)


def test_annualized_return_rejects_total_loss():
    returns = pd.Series([0.10, -1.0, 0.20])

    with pytest.raises(ValueError, match="greater than -100%"):
        annualized_return(returns)


@pytest.mark.parametrize("periods", [0, -1])
def test_annualized_return_rejects_non_positive_periods(periods):
    returns = pd.Series([0.01, 0.02])

    with pytest.raises(ValueError, match="greater than zero"):
        annualized_return(
            returns,
            periods_per_year=periods,
        )


@pytest.mark.parametrize("periods", [252.5, "252", True])
def test_annualized_return_rejects_non_integer_periods(periods):
    returns = pd.Series([0.01, 0.02])

    with pytest.raises(TypeError, match="integer"):
        annualized_return(
            returns,
            periods_per_year=periods,
        )


@pytest.mark.parametrize(
    ("initial_value", "final_value", "years"),
    [
        ("100", 120.0, 2.0),
        (100.0, "120", 2.0),
        (100.0, 120.0, "2"),
        (True, 120.0, 2.0),
    ],
)
def test_cagr_rejects_non_numeric_inputs(
    initial_value,
    final_value,
    years,
):
    with pytest.raises(TypeError, match="numeric"):
        cagr(
            initial_value,
            final_value,
            years,
        )


@pytest.mark.parametrize(
    ("initial_value", "final_value", "years"),
    [
        (np.inf, 120.0, 2.0),
        (100.0, np.inf, 2.0),
        (100.0, 120.0, np.inf),
    ],
)
def test_cagr_rejects_non_finite_inputs(
    initial_value,
    final_value,
    years,
):
    with pytest.raises(ValueError, match="finite"):
        cagr(
            initial_value,
            final_value,
            years,
        )


@pytest.mark.parametrize("initial_value", [0.0, -100.0])
def test_cagr_rejects_non_positive_initial_value(initial_value):
    with pytest.raises(ValueError, match="initial_value"):
        cagr(
            initial_value,
            120.0,
            2.0,
        )


@pytest.mark.parametrize("final_value", [0.0, -120.0])
def test_cagr_rejects_non_positive_final_value(final_value):
    with pytest.raises(ValueError, match="final_value"):
        cagr(
            100.0,
            final_value,
            2.0,
        )


def test_sharpe_rejects_non_numeric_risk_free_rate():
    returns = pd.Series([0.01, 0.02, 0.03])

    with pytest.raises(TypeError, match="risk_free_rate"):
        sharpe_ratio(
            returns,
            risk_free_rate="0.02",
        )


def test_sharpe_rejects_non_finite_risk_free_rate():
    returns = pd.Series([0.01, 0.02, 0.03])

    with pytest.raises(ValueError, match="finite"):
        sharpe_ratio(
            returns,
            risk_free_rate=np.inf,
        )


def test_sharpe_rejects_no_valid_observations():
    returns = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        sharpe_ratio(returns)


def test_sortino_rejects_non_numeric_target():
    returns = pd.Series([0.01, -0.02])

    with pytest.raises(TypeError, match="target_return"):
        sortino_ratio(
            returns,
            target_return="0.01",
        )


def test_sortino_rejects_non_finite_target():
    returns = pd.Series([0.01, -0.02])

    with pytest.raises(ValueError, match="finite"):
        sortino_ratio(
            returns,
            target_return=np.inf,
        )


def test_sortino_rejects_no_valid_observations():
    returns = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        sortino_ratio(returns)


def test_calmar_without_drawdown_returns_nan():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = calmar_ratio(
        returns,
        periods_per_year=1,
    )

    assert np.isnan(result)


def test_tracking_error_rejects_no_valid_active_returns():
    portfolio = pd.Series([np.nan, np.nan])
    benchmark = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        tracking_error(
            portfolio,
            benchmark,
        )


def test_information_ratio_rejects_mismatched_indices():
    portfolio = pd.Series(
        [0.01, 0.02],
        index=pd.date_range("2026-01-01", periods=2),
    )

    benchmark = pd.Series(
        [0.01, 0.02],
        index=pd.date_range("2026-01-02", periods=2),
    )

    with pytest.raises(ValueError, match="indices must match"):
        information_ratio(
            portfolio,
            benchmark,
        )


def test_information_ratio_rejects_no_valid_active_returns():
    portfolio = pd.Series([np.nan, np.nan])
    benchmark = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        information_ratio(
            portfolio,
            benchmark,
        )
