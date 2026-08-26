from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.production.config import EngineConfig


@dataclass(slots=True, frozen=True)
class ProductionValidationResult:
    """Validation summary for one production-engine input set."""

    observations: int
    strategy_count: int
    benchmark_present: bool
    missing_price_values: int
    missing_strategy_values: int
    missing_benchmark_values: int

    @property
    def has_missing_data(self) -> bool:
        return (
            self.missing_price_values > 0
            or self.missing_strategy_values > 0
            or self.missing_benchmark_values > 0
        )


def _require_datetime_index(
    index: pd.Index,
    *,
    name: str,
) -> None:
    if not isinstance(
        index,
        pd.DatetimeIndex,
    ):
        raise TypeError(f"{name} index must be a pandas DatetimeIndex.")

    if index.hasnans:
        raise ValueError(f"{name} index cannot contain missing timestamps.")

    if not index.is_unique:
        raise ValueError(f"{name} index must be unique.")

    if not index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be sorted.")


def _validate_numeric_series(
    values: pd.Series,
    *,
    name: str,
    allow_missing: bool,
) -> pd.Series:
    if not isinstance(
        values,
        pd.Series,
    ):
        raise TypeError(f"{name} must be a pandas Series.")

    if values.empty:
        raise ValueError(f"{name} cannot be empty.")

    try:
        result = values.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must contain numeric values.") from error

    array = result.to_numpy(dtype=float)

    missing = np.isnan(array)

    if not allow_missing and missing.any():
        raise ValueError(f"{name} cannot contain missing values.")

    non_missing = array[~missing]

    if not np.isfinite(non_missing).all():
        raise ValueError(f"{name} must contain only finite values.")

    return result


def _validate_numeric_frame(
    values: pd.DataFrame,
    *,
    name: str,
    allow_missing: bool,
) -> pd.DataFrame:
    if not isinstance(
        values,
        pd.DataFrame,
    ):
        raise TypeError(f"{name} must be a pandas DataFrame.")

    if values.empty:
        raise ValueError(f"{name} cannot be empty.")

    if values.columns.has_duplicates:
        raise ValueError(f"{name} columns must be unique.")

    if not all(isinstance(column, str) and column.strip() for column in values.columns):
        raise ValueError(f"{name} columns must be non-empty strings.")

    try:
        result = values.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must contain numeric values.") from error

    array = result.to_numpy(dtype=float)

    missing = np.isnan(array)

    if not allow_missing and missing.any():
        raise ValueError(f"{name} cannot contain missing values.")

    non_missing = array[~missing]

    if not np.isfinite(non_missing).all():
        raise ValueError(f"{name} must contain only finite values.")

    return result


def validate_production_inputs(
    *,
    prices: pd.Series,
    strategy_returns: pd.DataFrame,
    config: EngineConfig,
    benchmark_returns: pd.Series | None = None,
) -> ProductionValidationResult:
    """Validate production-engine inputs before execution."""
    if not isinstance(
        config,
        EngineConfig,
    ):
        raise TypeError("config must be an EngineConfig.")

    allow_missing = not config.fail_on_missing_data

    price_series = _validate_numeric_series(
        prices,
        name="prices",
        allow_missing=allow_missing,
    )

    strategy_frame = _validate_numeric_frame(
        strategy_returns,
        name="strategy_returns",
        allow_missing=allow_missing,
    )

    _require_datetime_index(
        price_series.index,
        name="prices",
    )

    _require_datetime_index(
        strategy_frame.index,
        name="strategy_returns",
    )

    if not price_series.index.equals(strategy_frame.index):
        raise ValueError("prices and strategy_returns must have matching indexes.")

    if len(price_series) < max(
        config.research.volatility_window + 1,
        config.research.trend_window,
        config.research.momentum_lookback + 1,
    ):
        raise ValueError("insufficient observations for configured research windows.")

    finite_prices = price_series.dropna()

    if (finite_prices <= 0).any():
        raise ValueError("prices must be strictly positive.")

    benchmark_series: pd.Series | None = None

    if benchmark_returns is not None:
        benchmark_series = _validate_numeric_series(
            benchmark_returns,
            name="benchmark_returns",
            allow_missing=allow_missing,
        )

        _require_datetime_index(
            benchmark_series.index,
            name="benchmark_returns",
        )

        if not benchmark_series.index.equals(price_series.index):
            raise ValueError("benchmark_returns index must match prices index.")

    missing_prices = int(price_series.isna().sum())

    missing_strategies = int(strategy_frame.isna().sum().sum())

    missing_benchmark = 0

    if benchmark_series is not None:
        missing_benchmark = int(benchmark_series.isna().sum())

    return ProductionValidationResult(
        observations=len(price_series),
        strategy_count=len(strategy_frame.columns),
        benchmark_present=(benchmark_series is not None),
        missing_price_values=missing_prices,
        missing_strategy_values=missing_strategies,
        missing_benchmark_values=missing_benchmark,
    )


def sanitize_missing_data(
    *,
    prices: pd.Series,
    strategy_returns: pd.DataFrame,
    benchmark_returns: pd.Series | None = None,
) -> tuple[
    pd.Series,
    pd.DataFrame,
    pd.Series | None,
]:
    """Remove rows containing missing values across production inputs."""
    if not isinstance(
        prices,
        pd.Series,
    ):
        raise TypeError("prices must be a pandas Series.")

    if not isinstance(
        strategy_returns,
        pd.DataFrame,
    ):
        raise TypeError("strategy_returns must be a pandas DataFrame.")

    if benchmark_returns is not None and not isinstance(
        benchmark_returns,
        pd.Series,
    ):
        raise TypeError("benchmark_returns must be a pandas Series.")

    frame = pd.DataFrame(
        {
            "__price__": prices,
        },
        index=prices.index,
    )

    for column in strategy_returns.columns:
        frame[f"__strategy__{column}"] = strategy_returns[column]

    if benchmark_returns is not None:
        frame["__benchmark__"] = benchmark_returns

    cleaned = frame.dropna(
        axis=0,
        how="any",
    )

    if cleaned.empty:
        raise ValueError("no observations remain after removing missing data.")

    clean_prices = cleaned["__price__"].astype(float)

    strategy_columns = [
        column for column in cleaned.columns if column.startswith("__strategy__")
    ]

    clean_strategies = cleaned[strategy_columns].copy()

    clean_strategies.columns = [
        column.removeprefix("__strategy__") for column in strategy_columns
    ]

    clean_benchmark: pd.Series | None = None

    if benchmark_returns is not None:
        clean_benchmark = cleaned["__benchmark__"].astype(float)

    return (
        clean_prices,
        clean_strategies,
        clean_benchmark,
    )


def validate_initial_equity(
    value: float,
) -> float:
    """Validate initial-equity input used by production interfaces."""
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError("initial_equity must be numeric.")

    result = float(value)

    if not math.isfinite(result):
        raise ValueError("initial_equity must be finite.")

    if result <= 0:
        raise ValueError("initial_equity must be greater than zero.")

    return result
