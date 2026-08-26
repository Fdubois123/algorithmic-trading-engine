import trading_engine
from trading_engine import (
    backtest,
    indicators,
    performance,
    portfolio,
    risk,
    stat_arb,
)

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


EXPECTED_BACKTEST = {
    "BacktestEngine",
    "BacktestResult",
    "ExecutionModel",
    "Fill",
    "FillEvent",
    "MarketEvent",
    "Order",
    "OrderEvent",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Portfolio",
    "Position",
    "QuantBacktestEngine",
    "SignalEvent",
    "Strategy",
}


EXPECTED_PORTFOLIO = {
    "black_litterman_posterior",
    "black_litterman_weights",
    "bounded_minimum_variance_weights",
    "default_view_uncertainty",
    "diversification_gain",
    "diversification_ratio",
    "effective_number_of_assets",
    "effective_number_of_risk_bets",
    "enforce_turnover_limit",
    "equal_weight_portfolio",
    "exponentially_weighted_covariance",
    "marginal_risk_contributions",
    "market_implied_returns",
    "maximum_sharpe_weights",
    "minimum_variance_weights",
    "percentage_risk_contributions",
    "portfolio_return",
    "portfolio_turnover",
    "portfolio_variance",
    "portfolio_volatility",
    "project_weights_to_bounded_simplex",
    "risk_concentration",
    "risk_contributions",
    "risk_parity_weights",
    "sample_covariance",
    "sample_expected_returns",
    "validate_covariance_matrix",
    "validate_expected_returns",
    "validate_views",
    "validate_weight_bounds",
    "validate_weights",
    "weight_concentration",
}


EXPECTED_STAT_ARB = {
    "EngleGrangerDiagnostic",
    "HedgeRatioResult",
    "MeanReversionResult",
    "PairBacktestResult",
    "PairDiagnostics",
    "PairLegWeights",
    "PairPosition",
    "PairSignal",
    "PairsTradingStrategy",
    "RollingHedgeResult",
    "StationarityDiagnostic",
    "WalkForwardPairResult",
    "align_pair_prices",
    "backtest_pair",
    "backtest_pair_walk_forward",
    "construct_spread",
    "diagnose_pair",
    "engle_granger_diagnostic",
    "estimate_half_life",
    "estimate_hedge_ratio",
    "estimate_mean_reversion",
    "expanding_hedge_ratio",
    "generate_pair_positions",
    "pair_leg_weights",
    "pair_log_returns",
    "pair_price_correlation",
    "pair_share_quantities",
    "residual_adf_statistic",
    "rolling_hedge_ratio",
    "rolling_spread_zscore",
    "validate_price_series",
    "walk_forward_spread",
    "walk_forward_zscore",
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


def test_backtest_public_api_exports_expected_symbols():
    assert set(backtest.__all__) == EXPECTED_BACKTEST


def test_backtest_public_api_symbols_are_importable():
    for name in backtest.__all__:
        assert hasattr(backtest, name)


def test_portfolio_public_api_exports_expected_symbols():
    assert set(portfolio.__all__) == EXPECTED_PORTFOLIO


def test_portfolio_public_api_symbols_are_importable():
    for name in portfolio.__all__:
        assert hasattr(portfolio, name)


def test_stat_arb_public_api_exports_expected_symbols():
    assert set(stat_arb.__all__) == EXPECTED_STAT_ARB


def test_stat_arb_public_api_symbols_are_importable():
    for name in stat_arb.__all__:
        assert hasattr(stat_arb, name)


def test_top_level_public_api_contains_all_public_symbols():
    expected = (
        EXPECTED_INDICATORS
        | EXPECTED_PERFORMANCE
        | EXPECTED_RISK
        | EXPECTED_BACKTEST
        | EXPECTED_PORTFOLIO
        | EXPECTED_STAT_ARB
    )

    assert set(trading_engine.__all__) == expected


def test_top_level_public_api_symbols_are_importable():
    for name in trading_engine.__all__:
        assert hasattr(trading_engine, name)
