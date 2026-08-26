from __future__ import annotations

import math
from dataclasses import dataclass


def _validate_positive(
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

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return float(value)


@dataclass(slots=True, frozen=True)
class ParticipationRateModel:
    """Restrict execution to a fraction of available bar volume."""

    max_participation_rate: float = 0.10

    def __post_init__(self) -> None:
        if isinstance(
            self.max_participation_rate,
            bool,
        ) or not isinstance(
            self.max_participation_rate,
            (int, float),
        ):
            raise TypeError("max_participation_rate must be numeric.")

        if not math.isfinite(float(self.max_participation_rate)):
            raise ValueError("max_participation_rate must be finite.")

        if not 0 < self.max_participation_rate <= 1:
            raise ValueError(
                "max_participation_rate must be greater than 0 and at most 1."
            )

    def maximum_quantity(
        self,
        *,
        volume: float,
    ) -> float:
        volume = _validate_positive(
            volume,
            name="volume",
        )

        return float(volume * self.max_participation_rate)

    def executable_quantity(
        self,
        *,
        requested_quantity: float,
        volume: float,
    ) -> float:
        requested_quantity = _validate_positive(
            requested_quantity,
            name="requested_quantity",
        )

        maximum = self.maximum_quantity(
            volume=volume,
        )

        return float(
            min(
                requested_quantity,
                maximum,
            )
        )
