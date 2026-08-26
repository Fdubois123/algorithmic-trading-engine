import json

import numpy as np
import pandas as pd
import pytest

import trading_engine
from trading_engine import (
    EngineConfig,
    EngineResult,
    ResearchConfig,
    persist_engine_result,
    run_engine,
    verify_experiment_artifacts,
)


def market_prices(
    observations: int = 160,
) -> pd.Series:
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    x = np.arange(
        observations,
        dtype=float,
    )

    values = 100.0 + 0.15 * x + 2.5 * np.sin(x / 8.0) + 1.0 * np.cos(x / 17.0)

    return pd.Series(
        values,
        index=index,
        dtype=float,
        name="price",
    )


def generated_strategy_returns(
    index: pd.Index,
) -> pd.DataFrame:
    x = np.arange(
        len(index),
        dtype=float,
    )

    return pd.DataFrame(
        {
            "trend": (0.0004 + 0.008 * np.sin(x / 11.0)),
            "momentum": (0.0003 + 0.007 * np.cos(x / 13.0)),
            "mean_reversion": (-0.006 * np.sin(x / 7.0)),
            "volatility": (0.004 * np.sin(x / 4.0)),
            "stat_arb": (0.0002 + 0.004 * np.cos(x / 5.0)),
        },
        index=index,
    )


def generated_benchmark_returns(
    index: pd.Index,
) -> pd.Series:
    x = np.arange(
        len(index),
        dtype=float,
    )

    return pd.Series(
        (0.00025 + 0.003 * np.sin(x / 15.0)),
        index=index,
        dtype=float,
        name="benchmark",
    )


def production_config() -> EngineConfig:
    return EngineConfig(
        research=ResearchConfig(
            volatility_window=15,
            trend_window=30,
            momentum_lookback=15,
            low_volatility_quantile=0.25,
            high_volatility_quantile=0.75,
            trend_threshold=0.001,
            momentum_threshold=0.02,
            minimum_exposure=0.25,
            maximum_exposure=1.0,
            maximum_turnover=0.20,
            transaction_cost_bps=7.5,
        ),
        initial_equity=1_000_000.0,
        periods_per_year=252,
        benchmark_name="synthetic-benchmark",
        experiment_name="v1-e2e",
        fail_on_missing_data=True,
        deterministic=True,
        metadata={
            "suite": "end-to-end",
            "version": "1.0",
        },
    )


def run_full_engine() -> EngineResult:
    prices = market_prices()

    return run_engine(
        prices=prices,
        strategy_returns=(generated_strategy_returns(prices.index)),
        benchmark_returns=(generated_benchmark_returns(prices.index)),
        config=production_config(),
    )


def test_public_api_exposes_v1_engine():
    assert trading_engine.run_engine is run_engine

    assert trading_engine.EngineConfig is EngineConfig

    assert hasattr(
        trading_engine,
        "persist_engine_result",
    )

    assert hasattr(
        trading_engine,
        "verify_experiment_artifacts",
    )


def test_end_to_end_engine_returns_complete_result():
    result = run_full_engine()

    assert isinstance(
        result,
        EngineResult,
    )

    assert result.observations == 160

    assert np.isfinite(result.final_equity)

    assert np.isfinite(result.total_return)

    assert len(result.experiment_id) == 64


def test_end_to_end_research_outputs_align():
    result = run_full_engine()

    index = result.research.returns.index

    assert result.research.equity_curve.index.equals(index)

    assert result.research.gross_returns.index.equals(index)

    assert result.research.turnover.index.equals(index)

    assert result.research.transaction_costs.index.equals(index)

    assert result.research.applied_weights.index.equals(index)


def test_end_to_end_first_period_is_causal():
    result = run_full_engine()

    first_weights = result.research.applied_weights.iloc[0]

    assert np.allclose(
        first_weights.to_numpy(dtype=float),
        0.0,
    )

    assert result.research.gross_returns.iloc[0] == pytest.approx(0.0)


def test_end_to_end_turnover_is_non_negative():
    result = run_full_engine()

    assert (result.research.turnover >= 0.0).all()


def test_end_to_end_costs_are_non_negative():
    result = run_full_engine()

    assert (result.research.transaction_costs >= 0.0).all()

    assert result.research.transaction_costs.sum() >= 0.0


def test_end_to_end_report_is_complete():
    result = run_full_engine()

    assert not result.report.overview.empty

    assert {
        "rolling_volatility",
        "rolling_sharpe",
    } == set(result.report.rolling_metrics.columns)

    assert not result.report.strategy_ranking.empty

    assert not result.report.regime_ranking.empty


def test_end_to_end_summary_contains_benchmark():
    result = run_full_engine()

    assert result.summary.benchmark is not None

    assert np.isfinite(result.summary.benchmark.portfolio_total_return)

    assert np.isfinite(result.summary.benchmark.benchmark_total_return)


def test_end_to_end_metadata_is_deterministic():
    first = run_full_engine()
    second = run_full_engine()

    assert first.experiment_id == second.experiment_id

    assert first.metadata.config_fingerprint == second.metadata.config_fingerprint


def test_end_to_end_results_are_deterministic():
    first = run_full_engine()
    second = run_full_engine()

    assert np.allclose(
        first.research.returns.to_numpy(dtype=float),
        second.research.returns.to_numpy(dtype=float),
    )

    assert np.allclose(
        first.research.applied_weights.to_numpy(dtype=float),
        second.research.applied_weights.to_numpy(dtype=float),
    )


def test_end_to_end_artifact_round_trip(
    tmp_path,
):
    result = run_full_engine()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    assert directory.exists()

    assert verify_experiment_artifacts(directory)

    expected_files = {
        "manifest.json",
        "metadata.json",
        "result.json",
        "report.json",
        "summary.json",
    }

    assert {item.name for item in directory.iterdir()} == expected_files


def test_end_to_end_artifact_identity(
    tmp_path,
):
    result = run_full_engine()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))

    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))

    assert manifest["experiment_id"] == result.experiment_id

    assert metadata["experiment_id"] == result.experiment_id


def test_end_to_end_artifact_checksums_change_on_tampering(
    tmp_path,
):
    result = run_full_engine()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    assert verify_experiment_artifacts(directory)

    summary_path = directory / "summary.json"

    summary_path.write_text(
        "{}",
        encoding="utf-8",
    )

    assert not verify_experiment_artifacts(directory)


def test_end_to_end_overwrite_round_trip(
    tmp_path,
):
    result = run_full_engine()

    first = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    second = persist_engine_result(
        root=tmp_path,
        result=result,
        overwrite=True,
    )

    assert first == second

    assert verify_experiment_artifacts(second)
