from trading_engine import indicators


def test_indicator_public_api_exports_expected_symbols():
    expected = {
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

    assert set(indicators.__all__) == expected


def test_public_api_symbols_are_importable():
    for name in indicators.__all__:
        assert hasattr(indicators, name)


import trading_engine


def test_top_level_public_api_matches_indicator_api():
    assert set(trading_engine.__all__) == set(indicators.__all__)


def test_top_level_exports_are_importable():
    for name in trading_engine.__all__:
        assert hasattr(trading_engine, name)
