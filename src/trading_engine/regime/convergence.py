from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.regime.adaptive import (
    AdaptiveStrategyAllocator,
)
from trading_engine.regime.labels import MarketRegime


@dataclass(slots=True, frozen=True)
class AdaptiveConvergenceResult:
    """Result of a causal adaptive strategy convergence simulation."""

    returns: pd.Series
    gross_returns: pd.Series
    equity_curve: pd.Series
    target_weights: pd.DataFrame
    applied_weights: pd.DataFrame
    turnover: pd.Series
    transaction_costs: pd.Series
    gross_exposure: pd.Series
    cash_weight: pd.Series

    @property
    def periods(self) -> int:
        return len(self.returns)

    @property
    def final_equity(self) -> float:
        if self.equity_curve.empty:
            return 1.0

        return float(self.equity_curve.iloc[-1])

    @property
    def total_return(self) -> float:
        return self.final_equity - 1.0


def _validate_non_negative_numeric(
    value: float,
    *,
    name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    result = float(value)

    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")

    if result < 0:
        raise ValueError(f"{name} cannot be negative.")

    return result


def _validate_confidence(
    confidence: pd.Series | Sequence[float] | None,
    *,
    index: pd.Index,
) -> pd.Series:
    if confidence is None:
        return pd.Series(
            1.0,
            index=index,
            dtype=float,
            name="confidence",
        )

    if isinstance(confidence, pd.Series):
        if not confidence.index.equals(index):
            raise ValueError("confidence index must match strategy_returns index.")

        result = confidence.astype(float).copy()

    else:
        if isinstance(
            confidence,
            (str, bytes),
        ):
            raise TypeError("confidence must be a numeric sequence or pandas Series.")

        try:
            values = list(confidence)
        except TypeError as exc:
            raise TypeError(
                "confidence must be a numeric sequence or pandas Series."
            ) from exc

        if len(values) != len(index):
            raise ValueError("confidence length must match strategy_returns.")

        result = pd.Series(
            values,
            index=index,
            dtype=float,
            name="confidence",
        )

    values = result.to_numpy(dtype=float)

    if not np.all(np.isfinite(values)):
        raise ValueError("confidence must contain only finite values.")

    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("confidence values must be between 0 and 1.")

    result.name = "confidence"

    return result


def _validate_regimes(
    regimes: pd.Series | Sequence[MarketRegime],
    *,
    index: pd.Index,
) -> pd.Series:
    if isinstance(regimes, pd.Series):
        if not regimes.index.equals(index):
            raise ValueError("regimes index must match strategy_returns index.")

        result = regimes.copy()

    else:
        if isinstance(
            regimes,
            (str, bytes),
        ):
            raise TypeError("regimes must be a sequence of MarketRegime values.")

        try:
            values = list(regimes)
        except TypeError as exc:
            raise TypeError(
                "regimes must be a sequence of MarketRegime values."
            ) from exc

        if len(values) != len(index):
            raise ValueError("regimes length must match strategy_returns.")

        result = pd.Series(
            values,
            index=index,
            dtype=object,
            name="regime",
        )

    if not all(isinstance(value, MarketRegime) for value in result):
        raise TypeError("regimes must contain only MarketRegime values.")

    result.name = "regime"

    return result


def _validate_strategy_returns(
    strategy_returns: pd.DataFrame,
) -> pd.DataFrame:
    if not isinstance(
        strategy_returns,
        pd.DataFrame,
    ):
        raise TypeError("strategy_returns must be a pandas DataFrame.")

    if strategy_returns.empty:
        raise ValueError("strategy_returns cannot be empty.")

    if strategy_returns.columns.empty:
        raise ValueError("strategy_returns must contain at least one strategy.")

    if not strategy_returns.index.is_unique:
        raise ValueError("strategy_returns index must be unique.")

    if strategy_returns.columns.has_duplicates:
        raise ValueError("strategy_returns columns must be unique.")

    if not all(
        isinstance(column, str) and column.strip()
        for column in strategy_returns.columns
    ):
        raise ValueError("strategy_returns columns must be non-empty strategy names.")

    try:
        result = strategy_returns.astype(float).copy()
    except (TypeError, ValueError) as exc:
        raise TypeError("strategy_returns must contain numeric values.") from exc

    values = result.to_numpy(dtype=float)

    if not np.all(np.isfinite(values)):
        raise ValueError("strategy_returns must contain only finite values.")

    return result


def _build_target_weights(
    *,
    strategy_returns: pd.DataFrame,
    regimes: pd.Series,
    confidence: pd.Series,
    allocator: AdaptiveStrategyAllocator,
) -> tuple[
    pd.DataFrame,
    pd.Series,
    pd.Series,
]:
    """Build target weights projected onto available strategies."""
    rows: list[dict[str, float]] = []
    gross_exposure: list[float] = []
    cash_weight: list[float] = []

    strategy_names = list(strategy_returns.columns)

    for timestamp in strategy_returns.index:
        allocation = allocator.allocate(
            regime=regimes.loc[timestamp],
            confidence=float(confidence.loc[timestamp]),
        )

        available_weights = {
            name: float(
                allocation.weights.get(
                    name,
                    0.0,
                )
            )
            for name in strategy_names
        }

        available_total = float(sum(abs(value) for value in available_weights.values()))

        desired_exposure = float(allocation.gross_exposure)

        if available_total > 0.0 and desired_exposure > 0.0:
            scale = desired_exposure / available_total

            row = {
                name: float(value * scale) for name, value in available_weights.items()
            }

        else:
            row = {name: 0.0 for name in strategy_names}

        actual_exposure = float(sum(abs(value) for value in row.values()))

        rows.append(row)

        gross_exposure.append(actual_exposure)

        cash_weight.append(
            float(
                max(
                    1.0 - actual_exposure,
                    0.0,
                )
            )
        )

    return (
        pd.DataFrame(
            rows,
            index=strategy_returns.index,
            columns=strategy_names,
            dtype=float,
        ),
        pd.Series(
            gross_exposure,
            index=strategy_returns.index,
            dtype=float,
            name="gross_exposure",
        ),
        pd.Series(
            cash_weight,
            index=strategy_returns.index,
            dtype=float,
            name="cash_weight",
        ),
    )


def _causal_applied_weights(
    target_weights: pd.DataFrame,
) -> pd.DataFrame:
    """
    Shift target weights by one period.

    Information observed at time t therefore affects
    portfolio returns only from time t + 1.
    """
    return target_weights.shift(1).fillna(0.0).astype(float)


def _calculate_applied_turnover(
    applied_weights: pd.DataFrame,
) -> pd.Series:
    previous = applied_weights.shift(1).fillna(0.0)

    turnover = 0.5 * (applied_weights - previous).abs().sum(axis=1)

    turnover.name = "turnover"

    return turnover.astype(float)


def run_adaptive_convergence(
    *,
    strategy_returns: pd.DataFrame,
    regimes: pd.Series | Sequence[MarketRegime],
    confidence: pd.Series | Sequence[float] | None = None,
    base_weights: Mapping[str, float] | None = None,
    minimum_exposure: float = 0.25,
    maximum_exposure: float = 1.0,
    maximum_turnover: float = 0.25,
    transaction_cost_bps: float = 0.0,
) -> AdaptiveConvergenceResult:
    """
    Run a causal regime-aware adaptive strategy simulation.

    Regime information observed at period t determines target
    weights at t. Those weights are applied to strategy returns
    beginning at t + 1, preventing same-period look-ahead.
    """
    returns_frame = _validate_strategy_returns(strategy_returns)

    regime_series = _validate_regimes(
        regimes,
        index=returns_frame.index,
    )

    confidence_series = _validate_confidence(
        confidence,
        index=returns_frame.index,
    )

    transaction_cost_bps = _validate_non_negative_numeric(
        transaction_cost_bps,
        name="transaction_cost_bps",
    )

    allocator = AdaptiveStrategyAllocator(
        base_weights=base_weights,
        minimum_exposure=minimum_exposure,
        maximum_exposure=maximum_exposure,
        maximum_turnover=maximum_turnover,
    )

    (
        target_weights,
        _target_gross_exposure,
        _target_cash_weight,
    ) = _build_target_weights(
        strategy_returns=returns_frame,
        regimes=regime_series,
        confidence=confidence_series,
        allocator=allocator,
    )

    applied_weights = _causal_applied_weights(target_weights)

    gross_exposure = applied_weights.abs().sum(axis=1).astype(float)

    gross_exposure.name = "gross_exposure"

    cash_weight = (1.0 - gross_exposure).clip(lower=0.0)

    cash_weight = cash_weight.astype(float)

    cash_weight.name = "cash_weight"

    gross_returns = (applied_weights * returns_frame).sum(axis=1)

    gross_returns = gross_returns.astype(float)

    gross_returns.name = "gross_return"

    turnover = _calculate_applied_turnover(applied_weights)

    cost_rate = transaction_cost_bps / 10_000.0

    transaction_costs = (turnover * cost_rate).astype(float)

    transaction_costs.name = "transaction_cost"

    net_returns = (gross_returns - transaction_costs).astype(float)

    net_returns.name = "return"

    if np.any(net_returns.to_numpy(dtype=float) <= -1.0):
        raise ValueError("net period return cannot be less than or equal to -100%.")

    equity_curve = (1.0 + net_returns).cumprod()

    equity_curve = equity_curve.astype(float)

    equity_curve.name = "equity"

    return AdaptiveConvergenceResult(
        returns=net_returns,
        gross_returns=gross_returns,
        equity_curve=equity_curve,
        target_weights=target_weights,
        applied_weights=applied_weights,
        turnover=turnover,
        transaction_costs=transaction_costs,
        gross_exposure=gross_exposure,
        cash_weight=cash_weight,
    )
