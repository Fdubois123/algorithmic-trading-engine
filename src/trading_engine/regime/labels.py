from __future__ import annotations

from enum import Enum


class VolatilityRegime(str, Enum):
    """Volatility state of a market."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TrendRegime(str, Enum):
    """Directional trend state of a market."""

    BEAR = "bear"
    SIDEWAYS = "sideways"
    BULL = "bull"


class MarketRegime(str, Enum):
    """Composite volatility and trend market regime."""

    LOW_VOL_BEAR = "low_vol_bear"
    LOW_VOL_SIDEWAYS = "low_vol_sideways"
    LOW_VOL_BULL = "low_vol_bull"

    NORMAL_VOL_BEAR = "normal_vol_bear"
    NORMAL_VOL_SIDEWAYS = "normal_vol_sideways"
    NORMAL_VOL_BULL = "normal_vol_bull"

    HIGH_VOL_BEAR = "high_vol_bear"
    HIGH_VOL_SIDEWAYS = "high_vol_sideways"
    HIGH_VOL_BULL = "high_vol_bull"


def combine_regimes(
    volatility: VolatilityRegime,
    trend: TrendRegime,
) -> MarketRegime:
    """Combine volatility and trend states."""
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

    mapping = {
        (
            VolatilityRegime.LOW,
            TrendRegime.BEAR,
        ): MarketRegime.LOW_VOL_BEAR,
        (
            VolatilityRegime.LOW,
            TrendRegime.SIDEWAYS,
        ): MarketRegime.LOW_VOL_SIDEWAYS,
        (
            VolatilityRegime.LOW,
            TrendRegime.BULL,
        ): MarketRegime.LOW_VOL_BULL,
        (
            VolatilityRegime.NORMAL,
            TrendRegime.BEAR,
        ): MarketRegime.NORMAL_VOL_BEAR,
        (
            VolatilityRegime.NORMAL,
            TrendRegime.SIDEWAYS,
        ): MarketRegime.NORMAL_VOL_SIDEWAYS,
        (
            VolatilityRegime.NORMAL,
            TrendRegime.BULL,
        ): MarketRegime.NORMAL_VOL_BULL,
        (
            VolatilityRegime.HIGH,
            TrendRegime.BEAR,
        ): MarketRegime.HIGH_VOL_BEAR,
        (
            VolatilityRegime.HIGH,
            TrendRegime.SIDEWAYS,
        ): MarketRegime.HIGH_VOL_SIDEWAYS,
        (
            VolatilityRegime.HIGH,
            TrendRegime.BULL,
        ): MarketRegime.HIGH_VOL_BULL,
    }

    return mapping[
        (
            volatility,
            trend,
        )
    ]
