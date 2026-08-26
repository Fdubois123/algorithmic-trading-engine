from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from trading_engine.regime.drawdown import (
    DrawdownRegime,
    rolling_drawdown_regime,
)
from trading_engine.regime.labels import (
    TrendRegime,
    VolatilityRegime,
)
from trading_engine.regime.momentum import (
    MomentumRegime,
    rolling_momentum_regime,
)


@dataclass(slots=True, frozen=True)
class CompositeRegimeObservation:
    """Composite regime score for one observation."""

    score: float
    confidence: float
    risk_on: bool
    risk_off: bool


def score_regime(
    *,
    volatility: VolatilityRegime,
    trend: TrendRegime,
    drawdown: DrawdownRegime,
    momentum: MomentumRegime,
) -> CompositeRegimeObservation:
    """Score a market state on a normalized risk-on/risk-off scale."""
    if not isinstance(
        volatility,
        VolatilityRegime,
    ):
        raise TypeError("volatility must be a VolatilityRegime.")

    if not isinstance(
        trend,
        TrendRegime,
    ):
        raise TypeError("trend must be a TrendRegime.")

    if not isinstance(
        drawdown,
        DrawdownRegime,
    ):
        raise TypeError("drawdown must be a DrawdownRegime.")

    if not isinstance(
        momentum,
        MomentumRegime,
    ):
        raise TypeError("momentum must be a MomentumRegime.")

    volatility_score = {
        VolatilityRegime.LOW: 1.0,
        VolatilityRegime.NORMAL: 0.0,
        VolatilityRegime.HIGH: -1.0,
    }[volatility]

    trend_score = {
        TrendRegime.BULL: 1.0,
        TrendRegime.SIDEWAYS: 0.0,
        TrendRegime.BEAR: -1.0,
    }[trend]

    drawdown_score = {
        DrawdownRegime.SHALLOW: 1.0,
        DrawdownRegime.MODERATE: 0.0,
        DrawdownRegime.DEEP: -1.0,
    }[drawdown]

    momentum_score = {
        MomentumRegime.POSITIVE: 1.0,
        MomentumRegime.NEUTRAL: 0.0,
        MomentumRegime.NEGATIVE: -1.0,
    }[momentum]

    score = (volatility_score + trend_score + drawdown_score + momentum_score) / 4.0

    confidence = abs(score)

    return CompositeRegimeObservation(
        score=float(score),
        confidence=float(confidence),
        risk_on=score >= 0.5,
        risk_off=score <= -0.5,
    )


def enrich_regime_frame(
    frame: pd.DataFrame,
    *,
    momentum_lookback: int = 20,
    momentum_threshold: float = 0.02,
    moderate_drawdown: float = -0.10,
    deep_drawdown: float = -0.20,
) -> pd.DataFrame:
    """Add momentum, drawdown and composite regime features."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError("frame must be a pandas DataFrame.")

    required = {
        "price",
        "volatility_regime",
        "trend_regime",
        "market_regime",
    }

    missing = required - set(frame.columns)

    if missing:
        raise ValueError("frame is missing required regime columns.")

    result = frame.copy()

    result["drawdown_regime"] = rolling_drawdown_regime(
        result["price"],
        moderate_threshold=moderate_drawdown,
        deep_threshold=deep_drawdown,
    )

    result["momentum_regime"] = rolling_momentum_regime(
        result["price"],
        lookback=momentum_lookback,
        threshold=momentum_threshold,
    )

    scores: list[float | None] = []

    confidence: list[float | None] = []

    risk_on: list[bool | None] = []

    risk_off: list[bool | None] = []

    for _, row in result.iterrows():
        values = (
            row["volatility_regime"],
            row["trend_regime"],
            row["drawdown_regime"],
            row["momentum_regime"],
        )

        if any(pd.isna(value) for value in values):
            scores.append(None)
            confidence.append(None)
            risk_on.append(None)
            risk_off.append(None)
            continue

        observation = score_regime(
            volatility=VolatilityRegime(row["volatility_regime"]),
            trend=TrendRegime(row["trend_regime"]),
            drawdown=DrawdownRegime(row["drawdown_regime"]),
            momentum=MomentumRegime(row["momentum_regime"]),
        )

        scores.append(observation.score)

        confidence.append(observation.confidence)

        risk_on.append(observation.risk_on)

        risk_off.append(observation.risk_off)

    result["regime_score"] = scores

    result["regime_confidence"] = confidence

    result["risk_on"] = risk_on

    result["risk_off"] = risk_off

    return result
