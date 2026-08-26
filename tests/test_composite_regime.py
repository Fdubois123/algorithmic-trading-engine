import numpy as np
import pandas as pd
import pytest

from trading_engine.regime import (
    DrawdownRegime,
    MomentumRegime,
    TrendRegime,
    VolatilityRegime,
    enrich_regime_frame,
    score_regime,
)


def test_strong_risk_on_regime():
    result = score_regime(
        volatility=VolatilityRegime.LOW,
        trend=TrendRegime.BULL,
        drawdown=DrawdownRegime.SHALLOW,
        momentum=MomentumRegime.POSITIVE,
    )

    assert result.score == pytest.approx(1.0)

    assert result.confidence == pytest.approx(1.0)

    assert result.risk_on
    assert not result.risk_off


def test_strong_risk_off_regime():
    result = score_regime(
        volatility=VolatilityRegime.HIGH,
        trend=TrendRegime.BEAR,
        drawdown=DrawdownRegime.DEEP,
        momentum=MomentumRegime.NEGATIVE,
    )

    assert result.score == pytest.approx(-1.0)

    assert result.risk_off
    assert not result.risk_on


def test_mixed_regime_has_lower_confidence():
    result = score_regime(
        volatility=VolatilityRegime.LOW,
        trend=TrendRegime.BEAR,
        drawdown=DrawdownRegime.SHALLOW,
        momentum=MomentumRegime.NEGATIVE,
    )

    assert result.confidence < 1.0


def test_invalid_component_type_rejected():
    with pytest.raises(
        TypeError,
        match="VolatilityRegime",
    ):
        score_regime(
            volatility="low",
            trend=TrendRegime.BULL,
            drawdown=DrawdownRegime.SHALLOW,
            momentum=MomentumRegime.POSITIVE,
        )


def regime_frame():
    index = pd.date_range(
        "2026-01-01",
        periods=50,
        freq="D",
    )

    price = np.linspace(
        100,
        130,
        50,
    ) + np.sin(np.arange(50))

    return pd.DataFrame(
        {
            "price": price,
            "volatility_regime": ["normal"] * 50,
            "trend_regime": ["bull"] * 50,
            "market_regime": ["normal_vol_bull"] * 50,
        },
        index=index,
    )


def test_enrich_regime_frame():
    result = enrich_regime_frame(
        regime_frame(),
        momentum_lookback=5,
    )

    assert {
        "drawdown_regime",
        "momentum_regime",
        "regime_score",
        "regime_confidence",
        "risk_on",
        "risk_off",
    }.issubset(result.columns)


def test_enrich_requires_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        enrich_regime_frame([])


def test_enrich_requires_regime_columns():
    with pytest.raises(
        ValueError,
        match="missing",
    ):
        enrich_regime_frame(
            pd.DataFrame(
                {
                    "price": [
                        100,
                        101,
                    ]
                }
            )
        )
