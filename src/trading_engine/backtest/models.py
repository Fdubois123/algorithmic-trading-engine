from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


def _validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string.")

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("symbol cannot be empty.")

    return symbol


def _validate_positive_number(
    value: float,
    *,
    name: str,
) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric.")

    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite.")

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")


@dataclass(slots=True)
class Order:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    status: OrderStatus = OrderStatus.CREATED
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        self.symbol = _validate_symbol(self.symbol)

        _validate_positive_number(
            self.quantity,
            name="quantity",
        )

        if not isinstance(self.side, OrderSide):
            raise TypeError("side must be an OrderSide.")

        if not isinstance(self.order_type, OrderType):
            raise TypeError("order_type must be an OrderType.")

        if not isinstance(self.status, OrderStatus):
            raise TypeError("status must be an OrderStatus.")

        if self.order_type is OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("limit_price is required for LIMIT orders.")

            _validate_positive_number(
                self.limit_price,
                name="limit_price",
            )

        elif self.limit_price is not None:
            raise ValueError("limit_price is only valid for LIMIT orders.")

        if self.timestamp is not None and not isinstance(
            self.timestamp,
            datetime,
        ):
            raise TypeError("timestamp must be a datetime or None.")


@dataclass(slots=True, frozen=True)
class Fill:
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float = 0.0
    slippage_cost: float = 0.0
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "symbol",
            _validate_symbol(self.symbol),
        )

        _validate_positive_number(
            self.quantity,
            name="quantity",
        )

        _validate_positive_number(
            self.price,
            name="price",
        )

        if not isinstance(self.side, OrderSide):
            raise TypeError("side must be an OrderSide.")

        for name, value in {
            "commission": self.commission,
            "slippage_cost": self.slippage_cost,
        }.items():
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(f"{name} must be numeric.")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")

            if value < 0:
                raise ValueError(f"{name} cannot be negative.")

    @property
    def notional(self) -> float:
        return float(self.quantity * self.price)

    @property
    def execution_cost(self) -> float:
        return float(self.commission + self.slippage_cost)


@dataclass(slots=True)
class Position:
    symbol: str
    quantity: float = 0.0
    average_price: float = 0.0
    realized_pnl: float = 0.0
    last_price: float | None = None

    def __post_init__(self) -> None:
        self.symbol = _validate_symbol(self.symbol)

    @property
    def is_flat(self) -> bool:
        return self.quantity == 0

    @property
    def market_value(self) -> float:
        if self.last_price is None:
            return 0.0

        return float(self.quantity * self.last_price)

    @property
    def unrealized_pnl(self) -> float:
        if self.is_flat or self.last_price is None:
            return 0.0

        return float(self.quantity * (self.last_price - self.average_price))

    def mark(self, price: float) -> None:
        _validate_positive_number(
            price,
            name="price",
        )

        self.last_price = float(price)

    def apply_fill(self, fill: Fill) -> None:
        if fill.symbol != self.symbol:
            raise ValueError("Fill symbol does not match position symbol.")

        signed_fill = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity

        old_quantity = self.quantity
        new_quantity = old_quantity + signed_fill

        same_direction = (
            old_quantity == 0
            or (old_quantity > 0 and signed_fill > 0)
            or (old_quantity < 0 and signed_fill < 0)
        )

        if same_direction:
            total_old_cost = abs(old_quantity) * self.average_price
            total_new_cost = abs(signed_fill) * fill.price

            total_quantity = abs(old_quantity) + abs(signed_fill)

            self.average_price = (total_old_cost + total_new_cost) / total_quantity

        else:
            closing_quantity = min(
                abs(old_quantity),
                abs(signed_fill),
            )

            if old_quantity > 0:
                pnl = (fill.price - self.average_price) * closing_quantity
            else:
                pnl = (self.average_price - fill.price) * closing_quantity

            self.realized_pnl += pnl

            if new_quantity == 0:
                self.average_price = 0.0

            elif old_quantity > 0 > new_quantity or old_quantity < 0 < new_quantity:
                self.average_price = fill.price

        self.quantity = float(new_quantity)
        self.last_price = float(fill.price)
