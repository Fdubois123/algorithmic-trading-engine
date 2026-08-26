from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)
from trading_engine.stat_arb.rolling import (
    RollingHedgeResult,
    expanding_hedge_ratio,
    rolling_hedge_ratio,
    walk_forward_spread,
)
from trading_engine.stat_arb.sizing import (
    pair_leg_weights,
)
from trading_engine.stat_arb.strategy import (
    PairPosition,
    PairsTradingStrategy,
)


@dataclass(slots=True, frozen=True)
class WalkForwardPairResult:
    """Walk-forward pairs-trading backtest result."""

    frame: pd.DataFrame
    initial_capital: float
    hedge_method: str
    estimation_window: int

    @property
    def final_equity(self) -> float:
        return float(self.frame["equity"].iloc[-1])

    @property
    def total_return(self) -> float:
        return self.final_equity / self.initial_capital - 1.0

    @property
    def observations(self) -> int:
        return len(self.frame)


def _validate_positive_number(
    value: float,
    *,
    name: str,
    allow_zero: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
    elif value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def _validate_zscore_window(
    zscore_window: int,
) -> int:
    if isinstance(
        zscore_window,
        bool,
    ) or not isinstance(
        zscore_window,
        int,
    ):
        raise TypeError("zscore_window must be an integer.")

    if zscore_window < 2:
        raise ValueError("zscore_window must be at least 2.")

    return zscore_window


def walk_forward_zscore(
    spread: pd.Series,
    *,
    window: int,
) -> pd.Series:
    """Calculate z-scores using only trailing observations through t."""
    window = _validate_zscore_window(window)

    if not isinstance(
        spread,
        pd.Series,
    ):
        raise TypeError("spread must be a pandas Series.")

    if spread.empty:
        raise ValueError("spread cannot be empty.")

    values = spread.astype(float)

    result = pd.Series(
        np.nan,
        index=values.index,
        dtype=float,
        name="walk_forward_zscore",
    )

    for index in range(
        window - 1,
        len(values),
    ):
        trailing = values.iloc[index - window + 1 : index + 1]

        if trailing.isna().any():
            continue

        standard_deviation = float(trailing.std(ddof=1))

        if standard_deviation <= 1e-15:
            continue

        result.iloc[index] = (
            float(trailing.iloc[-1] - trailing.mean()) / standard_deviation
        )

    return result


def _estimate_walk_forward_hedge(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    method: str,
    estimation_window: int,
) -> RollingHedgeResult:
    if method == "rolling":
        return rolling_hedge_ratio(
            dependent,
            independent,
            window=estimation_window,
        )

    if method == "expanding":
        return expanding_hedge_ratio(
            dependent,
            independent,
            minimum_observations=estimation_window,
        )

    raise ValueError("hedge_method must be 'rolling' or 'expanding'.")


def backtest_pair_walk_forward(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    hedge_method: str = "rolling",
    estimation_window: int = 60,
    zscore_window: int = 20,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float | None = 4.0,
    initial_capital: float = 100_000.0,
    gross_exposure: float = 1.0,
    transaction_cost_rate: float = 0.0,
) -> WalkForwardPairResult:
    """Run a causal walk-forward pairs backtest."""
    initial_capital = _validate_positive_number(
        initial_capital,
        name="initial_capital",
    )

    gross_exposure = _validate_positive_number(
        gross_exposure,
        name="gross_exposure",
        allow_zero=True,
    )

    transaction_cost_rate = _validate_positive_number(
        transaction_cost_rate,
        name="transaction_cost_rate",
        allow_zero=True,
    )

    if transaction_cost_rate >= 1:
        raise ValueError("transaction_cost_rate must be smaller than 1.")

    zscore_window = _validate_zscore_window(zscore_window)

    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=max(
            estimation_window,
            zscore_window,
            3,
        ),
    )

    hedge = _estimate_walk_forward_hedge(
        aligned["dependent"],
        aligned["independent"],
        method=hedge_method,
        estimation_window=estimation_window,
    )

    spread = walk_forward_spread(
        aligned["dependent"],
        aligned["independent"],
        hedge=hedge,
    )

    zscore = walk_forward_zscore(
        spread,
        window=zscore_window,
    )

    strategy = PairsTradingStrategy(
        entry_z=entry_z,
        exit_z=exit_z,
        stop_z=stop_z,
    )

    desired_dependent = np.zeros(
        len(aligned),
        dtype=float,
    )

    desired_independent = np.zeros(
        len(aligned),
        dtype=float,
    )

    states: list[str] = []

    for index, value in enumerate(zscore):
        beta = hedge.beta.iloc[index]

        if pd.isna(value) or pd.isna(beta) or beta <= 0:
            state = PairPosition.FLAT
            strategy.reset()
        else:
            state = strategy.update(float(value)).position

        states.append(state.value)

        if state is PairPosition.FLAT or pd.isna(beta) or beta <= 0:
            continue

        weights = pair_leg_weights(
            hedge_ratio=float(beta),
            position=state,
            gross_exposure=gross_exposure,
        )

        desired_dependent[index] = weights.dependent

        desired_independent[index] = weights.independent

    dependent_returns = (
        aligned["dependent"].pct_change().fillna(0.0).to_numpy(dtype=float)
    )

    independent_returns = (
        aligned["independent"].pct_change().fillna(0.0).to_numpy(dtype=float)
    )

    # Signal generated at t becomes exposure at t+1.
    active_dependent = np.roll(
        desired_dependent,
        1,
    )

    active_independent = np.roll(
        desired_independent,
        1,
    )

    active_dependent[0] = 0.0
    active_independent[0] = 0.0

    previous_dependent = np.roll(
        active_dependent,
        1,
    )

    previous_independent = np.roll(
        active_independent,
        1,
    )

    previous_dependent[0] = 0.0
    previous_independent[0] = 0.0

    turnover = np.abs(active_dependent - previous_dependent) + np.abs(
        active_independent - previous_independent
    )

    gross_return = (
        active_dependent * dependent_returns + active_independent * independent_returns
    )

    transaction_cost = turnover * transaction_cost_rate

    strategy_return = gross_return - transaction_cost

    equity = initial_capital * np.cumprod(1.0 + strategy_return)

    if not np.isfinite(equity).all():
        raise ValueError("walk-forward backtest produced non-finite equity.")

    frame = pd.DataFrame(
        {
            "dependent_price": aligned["dependent"].to_numpy(dtype=float),
            "independent_price": aligned["independent"].to_numpy(dtype=float),
            "alpha": hedge.alpha.to_numpy(dtype=float),
            "beta": hedge.beta.to_numpy(dtype=float),
            "spread": spread.to_numpy(dtype=float),
            "zscore": zscore.to_numpy(dtype=float),
            "position": states,
            "dependent_weight": active_dependent,
            "independent_weight": active_independent,
            "turnover": turnover,
            "gross_return": gross_return,
            "transaction_cost": transaction_cost,
            "strategy_return": strategy_return,
            "equity": equity,
        },
        index=aligned.index,
    )

    return WalkForwardPairResult(
        frame=frame,
        initial_capital=initial_capital,
        hedge_method=hedge_method,
        estimation_window=estimation_window,
    )
