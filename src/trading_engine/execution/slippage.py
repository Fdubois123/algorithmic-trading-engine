from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from trading_engine.backtest.models import OrderSide


def _validate_bps(
    value: float,
    *,
    name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite.")

    if value < 0:
        raise ValueError(f"{name} cannot be negative.")

    return float(value)


def _apply_adverse_bps(
    price: float,
    side: OrderSide,
    bps: float,
) -> float:
    fraction = bps / 10_000.0

    if side is OrderSide.BUY:
        return float(price * (1.0 + fraction))

    return float(price * (1.0 - fraction))


class SlippageModel(ABC):
    """Execution-price adjustment model."""

    @abstractmethod
    def adjust(
        self,
        *,
        market_price: float,
        side: OrderSide,
    ) -> float:
        raise NotImplementedError


@dataclass(slots=True, frozen=True)
class NoSlippage(SlippageModel):
    def adjust(
        self,
        *,
        market_price: float,
        side: OrderSide,
    ) -> float:
        return float(market_price)


@dataclass(slots=True, frozen=True)
class ConstantBpsSlippage(SlippageModel):
    """Adverse execution slippage in basis points."""

    bps: float = 0.0

    def __post_init__(self) -> None:
        _validate_bps(
            self.bps,
            name="bps",
        )

    def adjust(
        self,
        *,
        market_price: float,
        side: OrderSide,
    ) -> float:
        return _apply_adverse_bps(
            market_price,
            side,
            self.bps,
        )


@dataclass(slots=True, frozen=True)
class BidAskSpreadModel:
    """Cross half of a bid/ask spread during execution."""

    half_spread_bps: float = 0.0

    def __post_init__(self) -> None:
        _validate_bps(
            self.half_spread_bps,
            name="half_spread_bps",
        )

    def adjust(
        self,
        *,
        market_price: float,
        side: OrderSide,
    ) -> float:
        return _apply_adverse_bps(
            market_price,
            side,
            self.half_spread_bps,
        )
