import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    MeanReversionResult,
    estimate_half_life,
    estimate_mean_reversion,
)


def spread_series(
    values,
):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def mean_reverting_spread(
    *,
    phi=0.8,
    mean=5.0,
    observations=100,
):
    values = [10.0]

    shocks = np.sin(np.arange(observations - 1)) * 0.05

    for shock in shocks:
        next_value = mean + phi * (values[-1] - mean) + shock

        values.append(next_value)

    return spread_series(values)


def test_mean_reversion_result():
    result = estimate_mean_reversion(mean_reverting_spread())

    assert isinstance(
        result,
        MeanReversionResult,
    )

    assert 0 < result.autoregressive_coefficient < 1

    assert result.mean_reversion_speed > 0
    assert result.half_life > 0

    assert result.long_run_mean == pytest.approx(
        5.0,
        abs=0.2,
    )


def test_half_life_matches_full_result():
    spread = mean_reverting_spread()

    full = estimate_mean_reversion(spread)

    half_life = estimate_half_life(spread)

    assert half_life == pytest.approx(full.half_life)


def test_constant_spread_rejected():
    with pytest.raises(
        ValueError,
        match="non-zero lagged variance",
    ):
        estimate_mean_reversion(spread_series([5, 5, 5, 5]))


def test_short_spread_rejected():
    with pytest.raises(
        ValueError,
        match="enough observations",
    ):
        estimate_mean_reversion(spread_series([1, 2]))


def test_non_finite_spread_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        estimate_mean_reversion(spread_series([1, np.inf, 2]))


def test_spread_must_be_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        estimate_mean_reversion([1, 2, 3])


def test_explosive_process_rejected():
    values = [1.0]

    for _ in range(20):
        values.append(1.1 * values[-1] + 1.0)

    with pytest.raises(
        ValueError,
        match="stable positive mean reversion",
    ):
        estimate_mean_reversion(spread_series(values))
