import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    PairDiagnostics,
    diagnose_pair,
    pair_price_correlation,
)


def series(
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


def diagnostic_pair():
    x_values = np.linspace(
        50,
        100,
        100,
    )

    spread = [5.0]

    for index in range(99):
        shock = np.sin(index) * 0.05

        spread.append(5.0 + 0.8 * (spread[-1] - 5.0) + shock)

    x = series(x_values)

    y = series(2.0 * x_values + np.asarray(spread))

    return y, x


def test_pair_price_correlation():
    x = series([10, 11, 12, 13])

    y = series([20, 22, 24, 26])

    result = pair_price_correlation(
        x,
        y,
    )

    assert result == pytest.approx(1.0)


def test_constant_series_correlation_rejected():
    x = series([10, 10, 10, 10])

    y = series([20, 21, 22, 23])

    with pytest.raises(
        ValueError,
        match="non-zero variance",
    ):
        pair_price_correlation(
            x,
            y,
        )


def test_diagnose_pair():
    dependent, independent = diagnostic_pair()

    result = diagnose_pair(
        dependent,
        independent,
    )

    assert isinstance(
        result,
        PairDiagnostics,
    )

    assert result.observations == 100

    assert result.hedge.beta == pytest.approx(
        2.0,
        abs=0.1,
    )

    assert result.mean_reversion.half_life > 0

    assert -1 <= result.price_correlation <= 1

    assert result.spread_standard_deviation > 0
