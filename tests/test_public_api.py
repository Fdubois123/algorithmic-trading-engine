import trading_engine
from trading_engine import (
    backtest,
    indicators,
    performance,
    portfolio,
    production,
    regime,
    research,
    risk,
    stat_arb,
)

EXPECTED_INDICATORS = set(indicators.__all__)

EXPECTED_PERFORMANCE = set(performance.__all__)

EXPECTED_RISK = set(risk.__all__)

EXPECTED_BACKTEST = set(backtest.__all__)

EXPECTED_PORTFOLIO = set(portfolio.__all__)

EXPECTED_STAT_ARB = set(stat_arb.__all__)

EXPECTED_REGIME = set(regime.__all__)

EXPECTED_RESEARCH = set(research.__all__)

EXPECTED_PRODUCTION = {
    "EngineConfig",
    "EngineResult",
    "ProductionValidationResult",
    "experiment_directory",
    "load_manifest",
    "persist_engine_result",
    "run_engine",
    "sanitize_missing_data",
    "validate_initial_equity",
    "validate_production_inputs",
    "verify_experiment_artifacts",
}

EXPECTED_CONVERGENCE = {
    "AdaptiveConvergenceResult",
    "run_adaptive_convergence",
}


def test_indicator_public_api_symbols_are_importable():
    for name in indicators.__all__:
        assert hasattr(
            indicators,
            name,
        )


def test_performance_public_api_symbols_are_importable():
    for name in performance.__all__:
        assert hasattr(
            performance,
            name,
        )


def test_risk_public_api_symbols_are_importable():
    for name in risk.__all__:
        assert hasattr(
            risk,
            name,
        )


def test_backtest_public_api_symbols_are_importable():
    for name in backtest.__all__:
        assert hasattr(
            backtest,
            name,
        )


def test_portfolio_public_api_symbols_are_importable():
    for name in portfolio.__all__:
        assert hasattr(
            portfolio,
            name,
        )


def test_stat_arb_public_api_symbols_are_importable():
    for name in stat_arb.__all__:
        assert hasattr(
            stat_arb,
            name,
        )


def test_regime_public_api_symbols_are_importable():
    for name in regime.__all__:
        assert hasattr(
            regime,
            name,
        )


def test_research_public_api_symbols_are_importable():
    for name in research.__all__:
        assert hasattr(
            research,
            name,
        )


def test_production_public_api_exports_expected_symbols():
    assert set(production.__all__) == EXPECTED_PRODUCTION


def test_production_public_api_symbols_are_importable():
    for name in production.__all__:
        assert hasattr(
            production,
            name,
        )


def test_top_level_public_api_contains_all_public_symbols():
    expected = (
        EXPECTED_INDICATORS
        | EXPECTED_PERFORMANCE
        | EXPECTED_RISK
        | EXPECTED_BACKTEST
        | EXPECTED_PORTFOLIO
        | EXPECTED_STAT_ARB
        | EXPECTED_REGIME
        | EXPECTED_RESEARCH
        | EXPECTED_PRODUCTION
        | EXPECTED_CONVERGENCE
    )

    assert set(trading_engine.__all__) == expected


def test_top_level_public_api_symbols_are_importable():
    for name in trading_engine.__all__:
        assert hasattr(
            trading_engine,
            name,
        )


def test_top_level_engine_api_is_available():
    assert trading_engine.run_engine is production.run_engine

    assert trading_engine.EngineConfig is production.EngineConfig

    assert trading_engine.EngineResult is production.EngineResult


def test_top_level_research_api_is_available():
    assert trading_engine.run_research_experiment is research.run_research_experiment

    assert trading_engine.ResearchConfig is research.ResearchConfig

    assert trading_engine.ResearchResult is research.ResearchResult
