from __future__ import annotations

import numpy as np
import pandas as pd

from trading_engine.regime.composite import (
    enrich_regime_frame,
)
from trading_engine.regime.convergence import (
    run_adaptive_convergence,
)
from trading_engine.regime.detector import (
    detect_market_regimes,
)
from trading_engine.regime.labels import (
    MarketRegime,
)
from trading_engine.research.config import (
    ResearchConfig,
)
from trading_engine.research.result import (
    ResearchResult,
)


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

    try:
        values = strategy_returns.astype(float).copy()
    except (TypeError, ValueError) as error:
        raise TypeError("strategy_returns must contain numeric values.") from error

    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("strategy_returns must contain only finite values.")

    return values


def _extract_regimes(
    frame: pd.DataFrame,
) -> tuple[
    pd.Series,
    pd.Series,
]:
    market = frame["market_regime"]

    confidence = frame["regime_confidence"]

    valid = market.notna() & confidence.notna()

    if not valid.any():
        raise ValueError("regime detection produced no valid observations.")

    regimes = pd.Series(
        [
            (
                MarketRegime(value)
                if pd.notna(value)
                else MarketRegime.NORMAL_VOL_SIDEWAYS
            )
            for value in market
        ],
        index=frame.index,
        dtype=object,
        name="market_regime",
    )

    confidence_values = (
        confidence.fillna(0.0)
        .astype(float)
        .clip(
            lower=0.0,
            upper=1.0,
        )
    )

    return (
        regimes,
        confidence_values,
    )


def run_research_experiment(
    *,
    prices: pd.Series,
    strategy_returns: pd.DataFrame,
    config: ResearchConfig | None = None,
) -> ResearchResult:
    """Run the complete regime-aware adaptive research pipeline."""
    if config is None:
        config = ResearchConfig()

    if not isinstance(
        config,
        ResearchConfig,
    ):
        raise TypeError("config must be a ResearchConfig.")

    detection = detect_market_regimes(
        prices,
        volatility_window=config.volatility_window,
        trend_window=config.trend_window,
        low_volatility_quantile=(config.low_volatility_quantile),
        high_volatility_quantile=(config.high_volatility_quantile),
        trend_threshold=config.trend_threshold,
    )

    regime_frame = enrich_regime_frame(
        detection.frame,
        momentum_lookback=config.momentum_lookback,
        momentum_threshold=config.momentum_threshold,
    )

    returns_frame = _validate_strategy_returns(
        strategy_returns,
        index=regime_frame.index,
    )

    regimes, confidence = _extract_regimes(regime_frame)

    convergence = run_adaptive_convergence(
        strategy_returns=returns_frame,
        regimes=regimes,
        confidence=confidence,
        base_weights=config.base_weights,
        minimum_exposure=config.minimum_exposure,
        maximum_exposure=config.maximum_exposure,
        maximum_turnover=config.maximum_turnover,
        transaction_cost_bps=config.transaction_cost_bps,
    )

    return ResearchResult(
        equity_curve=convergence.equity_curve,
        returns=convergence.returns,
        gross_returns=convergence.gross_returns,
        regime_frame=regime_frame,
        target_weights=convergence.target_weights,
        applied_weights=convergence.applied_weights,
        turnover=convergence.turnover,
        transaction_costs=convergence.transaction_costs,
    )
