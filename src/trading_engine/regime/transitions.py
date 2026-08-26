from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True, frozen=True)
class RegimeTransition:
    """One detected regime transition."""

    index: object
    previous: str
    current: str
    persistence: int


def regime_transition_flags(
    regimes: pd.Series,
) -> pd.Series:
    """Return True whenever a valid regime changes."""
    if not isinstance(
        regimes,
        pd.Series,
    ):
        raise TypeError("regimes must be a pandas Series.")

    if regimes.empty:
        raise ValueError("regimes cannot be empty.")

    result = pd.Series(
        False,
        index=regimes.index,
        dtype=bool,
        name="regime_transition",
    )

    previous: object = None

    for index, value in enumerate(regimes):
        if pd.isna(value):
            continue

        if previous is not None and value != previous:
            result.iloc[index] = True

        previous = value

    return result


def regime_persistence(
    regimes: pd.Series,
) -> pd.Series:
    """Return consecutive bars spent in the current valid regime."""
    if not isinstance(
        regimes,
        pd.Series,
    ):
        raise TypeError("regimes must be a pandas Series.")

    if regimes.empty:
        raise ValueError("regimes cannot be empty.")

    result = pd.Series(
        0,
        index=regimes.index,
        dtype=int,
        name="regime_persistence",
    )

    previous: object = None
    count = 0

    for index, value in enumerate(regimes):
        if pd.isna(value):
            previous = None
            count = 0
            continue

        if value == previous:
            count += 1
        else:
            previous = value
            count = 1

        result.iloc[index] = count

    return result


def extract_regime_transitions(
    regimes: pd.Series,
) -> tuple[
    RegimeTransition,
    ...,
]:
    """Return explicit regime-transition records."""
    flags = regime_transition_flags(regimes)

    persistence = regime_persistence(regimes)

    transitions: list[RegimeTransition] = []

    previous: str | None = None

    for index, value in regimes.items():
        if pd.isna(value):
            continue

        current = str(value)

        if previous is not None and bool(flags.loc[index]):
            transitions.append(
                RegimeTransition(
                    index=index,
                    previous=previous,
                    current=current,
                    persistence=int(persistence.loc[index]),
                )
            )

        previous = current

    return tuple(transitions)
