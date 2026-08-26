from __future__ import annotations

import numpy as np
import pandas as pd

from trading_engine.production.config import (
    EngineConfig,
)
from trading_engine.production.result import (
    EngineResult,
)
from trading_engine.research import (
    build_experiment_metadata,
    build_experiment_summary,
    build_research_report,
    run_research_experiment,
)


def _validate_prices(
    prices: pd.Series,
) -> pd.Series:
    if not isinstance(
        prices,
        pd.Series,
    ):
        raise TypeError("prices must be a pandas Series.")

    if prices.empty:
        raise ValueError("prices cannot be empty.")

    try:
        result = prices.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError("prices must contain numeric values.") from error

    values = result.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("prices must contain only finite values.")

    if np.any(values <= 0):
        raise ValueError("prices must be strictly positive.")

    if not result.index.is_unique:
        raise ValueError("prices index must be unique.")

    if not result.index.is_monotonic_increasing:
        raise ValueError("prices index must be sorted.")

    return result


def _validate_strategy_returns(
    strategy_returns: pd.DataFrame,
    *,
    index: pd.Index,
) -> pd.DataFrame:
    if not isinstance(
        strategy_returns,
        pd.DataFrame,
    ):
        raise TypeError("strategy_returns must be a pandas DataFrame.")

    if strategy_returns.empty:
        raise ValueError("strategy_returns cannot be empty.")

    if not strategy_returns.index.equals(index):
        raise ValueError("strategy_returns index must match prices index.")

    if strategy_returns.columns.has_duplicates:
        raise ValueError("strategy_returns columns must be unique.")

    if not all(
        isinstance(column, str) and column.strip()
        for column in strategy_returns.columns
    ):
        raise ValueError("strategy_returns columns must be non-empty strings.")

    try:
        result = strategy_returns.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError("strategy_returns must contain numeric values.") from error

    if not np.isfinite(result.to_numpy(dtype=float)).all():
        raise ValueError("strategy_returns must contain only finite values.")

    return result


def _validate_benchmark(
    benchmark_returns: pd.Series | None,
    *,
    index: pd.Index,
) -> pd.Series | None:
    if benchmark_returns is None:
        return None

    if not isinstance(
        benchmark_returns,
        pd.Series,
    ):
        raise TypeError("benchmark_returns must be a pandas Series.")

    if not benchmark_returns.index.equals(index):
        raise ValueError("benchmark_returns index must match prices index.")

    try:
        result = benchmark_returns.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError("benchmark_returns must contain numeric values.") from error

    if not np.isfinite(result.to_numpy(dtype=float)).all():
        raise ValueError("benchmark_returns must contain only finite values.")

    return result


def run_engine(
    *,
    prices: pd.Series,
    strategy_returns: pd.DataFrame,
    config: EngineConfig | None = None,
    benchmark_returns: pd.Series | None = None,
) -> EngineResult:
    """Run the complete production research pipeline."""
    if config is None:
        config = EngineConfig()

    if not isinstance(
        config,
        EngineConfig,
    ):
        raise TypeError("config must be an EngineConfig.")

    price_series = _validate_prices(prices)

    returns_frame = _validate_strategy_returns(
        strategy_returns,
        index=price_series.index,
    )

    benchmark = _validate_benchmark(
        benchmark_returns,
        index=price_series.index,
    )

    research_result = run_research_experiment(
        prices=price_series,
        strategy_returns=returns_frame,
        config=config.research,
    )

    report = build_research_report(
        result=research_result,
        strategy_returns=returns_frame,
        periods_per_year=config.periods_per_year,
    )

    summary = build_experiment_summary(
        result=research_result,
        strategy_returns=returns_frame,
        benchmark_returns=benchmark,
    )

    metadata = build_experiment_metadata(
        config=config.research,
        observations=len(price_series),
        strategy_count=len(returns_frame.columns),
    )

    return EngineResult(
        research=research_result,
        report=report,
        summary=summary,
        metadata=metadata,
        benchmark_name=config.benchmark_name,
        experiment_name=config.experiment_name,
    )
