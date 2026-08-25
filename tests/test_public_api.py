import trading_engine
from trading_engine import indicators, performance, risk

EXPECTED_INDICATORS = {
    "annualized_volatility",
    "close_to_close_volatility",
    "cumulative_returns",
    "downside_volatility",
    "ewma_volatility",
    "historical_volatility",
    "log_returns",
    "parkinson_volatility",
    "rolling_beta",
    "rolling_correlation",
    "rolling_covariance",
    "rolling_mean",
    "rolling_std",
    "rolling_zscore",
    "simple_returns",
    "wealth_index",
}

EXPECTED_PERFORMANCE = {
    "annualized_return",
    "cagr",
    "calmar_ratio",
    "drawdown_duration",
    "drawdown_series",
    "information_ratio",
    "max_drawdown",
    "sharpe_ratio",
    "sortino_ratio",
    "tracking_error",
    "underwater_curve",
}

EXPECTED_RISK = {
    "historical_cvar",
    "historical_var",
}


def test_indicator_public_api_exports_expected_symbols():
    assert set(indicators.__all__) == EXPECTED_INDICATORS


def test_indicator_public_api_symbols_are_importable():
    for name in indicators.__all__:
        assert hasattr(indicators, name)


def test_performance_public_api_exports_expected_symbols():
    assert set(performance.__all__) == EXPECTED_PERFORMANCE


def test_performance_public_api_symbols_are_importable():
    for name in performance.__all__:
        assert hasattr(performance, name)


def test_risk_public_api_exports_expected_symbols():
    assert set(risk.__all__) == EXPECTED_RISK


def test_risk_public_api_symbols_are_importable():
    for name in risk.__all__:
        assert hasattr(risk, name)


def test_top_level_public_api_contains_all_public_symbols():
    expected = EXPECTED_INDICATORS | EXPECTED_PERFORMANCE | EXPECTED_RISK

    assert set(trading_engine.__all__) == expected


def test_top_level_public_api_symbols_are_importable():
    for name in trading_engine.__all__:
        assert hasattr(trading_engine, name)
