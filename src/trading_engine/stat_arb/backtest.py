from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.stat_arb.hedge import (
    estimate_hedge_ratio,
)
from trading_engine.stat_arb.pairs import (
    align_pair_prices,
)
from trading_engine.stat_arb.sizing import (
    pair_leg_weights,
)
from trading_engine.stat_arb.spread import (
    construct_spread,
    rolling_spread_zscore,
)
from trading_engine.stat_arb.strategy import (
    PairPosition,
    PairsTradingStrategy,
)


@dataclass(slots=True, frozen=True)
class PairBacktestResult:
    """Historical output of a pairs-trading backtest."""

    frame: pd.DataFrame
    hedge_ratio: float
    intercept: float
    initial_capital: float

    @property
    def final_equity(self) -> float:
        return float(self.frame["equity"].iloc[-1])

    @property
    def total_return(self) -> float:
        return self.final_equity / self.initial_capital - 1.0

    @property
    def observations(self) -> int:
        return len(self.frame)


def _validate_positive_numeric(
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


def backtest_pair(
    dependent: pd.Series,
    independent: pd.Series,
    *,
    window: int = 20,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float | None = 4.0,
    initial_capital: float = 100_000.0,
    gross_exposure: float = 1.0,
    transaction_cost_rate: float = 0.0,
) -> PairBacktestResult:
    """Backtest a static-hedge-ratio pairs-trading strategy."""
    initial_capital = _validate_positive_numeric(
        initial_capital,
        name="initial_capital",
    )

    gross_exposure = _validate_positive_numeric(
        gross_exposure,
        name="gross_exposure",
        allow_zero=True,
    )

    transaction_cost_rate = _validate_positive_numeric(
        transaction_cost_rate,
        name="transaction_cost_rate",
        allow_zero=True,
    )

    if transaction_cost_rate >= 1:
        raise ValueError("transaction_cost_rate must be smaller than 1.")

    aligned = align_pair_prices(
        dependent,
        independent,
        first_name="dependent",
        second_name="independent",
        minimum_observations=max(
            window + 1,
            3,
        ),
    )

    hedge = estimate_hedge_ratio(
        aligned["dependent"],
        aligned["independent"],
    )

    if hedge.beta <= 0:
        raise ValueError("pairs backtest requires a positive hedge ratio.")

    spread = construct_spread(
        aligned["dependent"],
        aligned["independent"],
        hedge_ratio=hedge.beta,
        intercept=hedge.alpha,
    )

    zscore = rolling_spread_zscore(
        spread,
        window=window,
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
        if pd.isna(value):
            state = PairPosition.FLAT
        else:
            state = strategy.update(float(value)).position

        states.append(state.value)

        weights = pair_leg_weights(
            hedge_ratio=hedge.beta,
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

    # Signals observed at t become holdings for t+1.
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
        raise ValueError("backtest produced non-finite equity.")

    frame = pd.DataFrame(
        {
            "dependent_price": (aligned["dependent"].to_numpy(dtype=float)),
            "independent_price": (aligned["independent"].to_numpy(dtype=float)),
            "spread": spread.to_numpy(dtype=float),
            "zscore": zscore.to_numpy(dtype=float),
            "position": states,
            "dependent_weight": (active_dependent),
            "independent_weight": (active_independent),
            "turnover": turnover,
            "gross_return": gross_return,
            "transaction_cost": (transaction_cost),
            "strategy_return": (strategy_return),
            "equity": equity,
        },
        index=aligned.index,
    )

    return PairBacktestResult(
        frame=frame,
        hedge_ratio=hedge.beta,
        intercept=hedge.alpha,
        initial_capital=initial_capital,
    )
