from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


def _validate_non_negative(
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


def _validate_positive(
    value: float,
    *,
    name: str,
) -> float:
    value = _validate_non_negative(
        value,
        name=name,
    )

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


class CommissionModel(ABC):
    """Base interface for transaction commission models."""

    @abstractmethod
    def calculate(
        self,
        *,
        quantity: float,
        price: float,
    ) -> float:
        """Return commission charged for an execution."""
        raise NotImplementedError


@dataclass(slots=True, frozen=True)
class NoCommission(CommissionModel):
    """Zero-commission execution."""

    def calculate(
        self,
        *,
        quantity: float,
        price: float,
    ) -> float:
        _validate_positive(
            quantity,
            name="quantity",
        )
        _validate_positive(
            price,
            name="price",
        )

        return 0.0


@dataclass(slots=True, frozen=True)
class FixedCommission(CommissionModel):
    """Fixed monetary commission per fill."""

    amount: float = 0.0

    def __post_init__(self) -> None:
        _validate_non_negative(
            self.amount,
            name="amount",
        )

    def calculate(
        self,
        *,
        quantity: float,
        price: float,
    ) -> float:
        _validate_positive(
            quantity,
            name="quantity",
        )
        _validate_positive(
            price,
            name="price",
        )

        return float(self.amount)


@dataclass(slots=True, frozen=True)
class PercentageCommission(CommissionModel):
    """Commission proportional to executed notional."""

    rate: float = 0.001

    def __post_init__(self) -> None:
        _validate_non_negative(
            self.rate,
            name="rate",
        )

    def calculate(
        self,
        *,
        quantity: float,
        price: float,
    ) -> float:
        quantity = _validate_positive(
            quantity,
            name="quantity",
        )
        price = _validate_positive(
            price,
            name="price",
        )

        return float(quantity * price * self.rate)


@dataclass(slots=True, frozen=True)
class PerShareCommission(CommissionModel):
    """Per-share commission with an optional minimum charge."""

    per_share: float = 0.005
    minimum: float = 0.0

    def __post_init__(self) -> None:
        _validate_non_negative(
            self.per_share,
            name="per_share",
        )
        _validate_non_negative(
            self.minimum,
            name="minimum",
        )

    def calculate(
        self,
        *,
        quantity: float,
        price: float,
    ) -> float:
        quantity = _validate_positive(
            quantity,
            name="quantity",
        )
        _validate_positive(
            price,
            name="price",
        )

        raw = quantity * self.per_share

        return float(max(raw, self.minimum))
