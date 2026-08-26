from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_engine.regime.labels import (
    MarketRegime,
    TrendRegime,
    VolatilityRegime,
    combine_regimes,
)
from trading_engine.regime.trend import (
    rolling_trend_regime,
    rolling_trend_strength,
)
from trading_engine.regime.volatility import (
    rolling_realized_volatility,
    rolling_volatility_regime,
)


@dataclass(slots=True, frozen=True)
class RegimeDetectionResult:
    """Output from composite market-regime detection."""

    frame: pd.DataFrame

    @property
    def observations(self) -> int:
        return len(self.frame)

    @property
    def latest_regime(
        self,
    ) -> MarketRegime | None:
        valid = self.frame["market_regime"].dropna()

        if valid.empty:
            return None

        return MarketRegime(valid.iloc[-1])


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
        values = prices.astype(float)
    except (TypeError, ValueError) as error:
        raise TypeError("prices must contain numeric values.") from error

    array = values.to_numpy(dtype=float)

    if not np.isfinite(array).all():
        raise ValueError("prices must contain only finite values.")

    if np.any(array <= 0):
        raise ValueError("prices must be strictly positive.")

    if not values.index.is_unique:
        raise ValueError("prices index must not contain duplicates.")

    if not values.index.is_monotonic_increasing:
        raise ValueError("prices index must be sorted.")

    return values


def price_returns(
    prices: pd.Series,
) -> pd.Series:
    """Calculate simple returns used by regime models."""
    values = _validate_prices(prices)

    returns = values.pct_change(fill_method=None)

    returns = returns.iloc[1:]

    returns.name = "returns"

    return returns


def detect_market_regimes(
    prices: pd.Series,
    *,
    volatility_window: int = 20,
    trend_window: int = 50,
    low_volatility_quantile: float = 0.25,
    high_volatility_quantile: float = 0.75,
    trend_threshold: float = 0.001,
    periods_per_year: int = 252,
) -> RegimeDetectionResult:
    """Detect causal composite volatility/trend regimes."""
    values = _validate_prices(prices)

    if len(values) < max(
        volatility_window + 1,
        trend_window,
    ):
        raise ValueError(
            "prices do not contain enough observations "
            "for the requested regime windows."
        )

    returns = price_returns(values)

    realized_volatility = rolling_realized_volatility(
        returns,
        window=volatility_window,
        periods_per_year=periods_per_year,
    )

    volatility_regime = rolling_volatility_regime(
        returns,
        window=volatility_window,
        low_quantile=low_volatility_quantile,
        high_quantile=high_volatility_quantile,
        periods_per_year=periods_per_year,
    )

    trend_strength = rolling_trend_strength(
        values,
        window=trend_window,
    )

    trend_regime = rolling_trend_regime(
        values,
        window=trend_window,
        threshold=trend_threshold,
    )

    frame = pd.DataFrame(
        index=values.index,
    )

    frame["price"] = values

    frame["return"] = returns.reindex(values.index)

    frame["realized_volatility"] = realized_volatility.reindex(values.index)

    frame["volatility_regime"] = volatility_regime.reindex(values.index)

    frame["trend_strength"] = trend_strength.reindex(values.index)

    frame["trend_regime"] = trend_regime.reindex(values.index)

    market_regimes: list[str | pd._libs.missing.NAType] = []

    for _, row in frame.iterrows():
        volatility_value = row["volatility_regime"]

        trend_value = row["trend_regime"]

        if pd.isna(volatility_value) or pd.isna(trend_value):
            market_regimes.append(pd.NA)
            continue

        combined = combine_regimes(
            VolatilityRegime(volatility_value),
            TrendRegime(trend_value),
        )

        market_regimes.append(combined.value)

    frame["market_regime"] = pd.Series(
        market_regimes,
        index=frame.index,
        dtype="object",
    )

    return RegimeDetectionResult(frame=frame)
