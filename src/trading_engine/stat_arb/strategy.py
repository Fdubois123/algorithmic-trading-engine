from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from trading_engine.stat_arb.spread import (
    rolling_spread_zscore,
)


class PairPosition(str, Enum):
    """State of a pairs-trading position."""

    FLAT = "flat"
    LONG_SPREAD = "long_spread"
    SHORT_SPREAD = "short_spread"


@dataclass(slots=True, frozen=True)
class PairSignal:
    """Signal emitted by a pairs-trading strategy."""

    position: PairPosition
    zscore: float
    changed: bool


def _validate_threshold(
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


class PairsTradingStrategy:
    """Stateful z-score pairs-trading strategy."""

    def __init__(
        self,
        *,
        entry_z: float = 2.0,
        exit_z: float = 0.5,
        stop_z: float | None = 4.0,
    ) -> None:
        self.entry_z = _validate_threshold(
            entry_z,
            name="entry_z",
        )

        self.exit_z = _validate_threshold(
            exit_z,
            name="exit_z",
            allow_zero=True,
        )

        if self.exit_z >= self.entry_z:
            raise ValueError("exit_z must be smaller than entry_z.")

        if stop_z is None:
            self.stop_z = None
        else:
            self.stop_z = _validate_threshold(
                stop_z,
                name="stop_z",
            )

            if self.stop_z <= self.entry_z:
                raise ValueError("stop_z must be greater than entry_z.")

        self._position = PairPosition.FLAT

    @property
    def position(self) -> PairPosition:
        """Return the current pair position."""
        return self._position

    def reset(self) -> None:
        """Reset the strategy to a flat state."""
        self._position = PairPosition.FLAT

    def update(
        self,
        zscore: float,
    ) -> PairSignal:
        """Update strategy state from the latest spread z-score."""
        if isinstance(zscore, bool) or not isinstance(
            zscore,
            (
                int,
                float,
                np.integer,
                np.floating,
            ),
        ):
            raise TypeError("zscore must be numeric.")

        zscore = float(zscore)

        if not math.isfinite(zscore):
            raise ValueError("zscore must be finite.")

        previous = self._position

        if self._position is PairPosition.FLAT:
            if zscore <= -self.entry_z:
                self._position = PairPosition.LONG_SPREAD

            elif zscore >= self.entry_z:
                self._position = PairPosition.SHORT_SPREAD

        elif (
            self._position is PairPosition.LONG_SPREAD
            and (
                (self.stop_z is not None and zscore <= -self.stop_z)
                or zscore >= -self.exit_z
            )
        ) or (
            self._position is PairPosition.SHORT_SPREAD
            and (
                (self.stop_z is not None and zscore >= self.stop_z)
                or zscore <= self.exit_z
            )
        ):
            self._position = PairPosition.FLAT

        return PairSignal(
            position=self._position,
            zscore=zscore,
            changed=(self._position is not previous),
        )


def generate_pair_positions(
    spread: pd.Series,
    *,
    window: int = 20,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float | None = 4.0,
) -> pd.Series:
    """Generate historical pair positions from a spread series."""
    zscores = rolling_spread_zscore(
        spread,
        window=window,
    )

    strategy = PairsTradingStrategy(
        entry_z=entry_z,
        exit_z=exit_z,
        stop_z=stop_z,
    )

    positions: list[str] = []

    for value in zscores:
        if pd.isna(value):
            positions.append(PairPosition.FLAT.value)
            continue

        signal = strategy.update(float(value))

        positions.append(signal.position.value)

    return pd.Series(
        positions,
        index=spread.index,
        name="pair_position",
        dtype="object",
    )
