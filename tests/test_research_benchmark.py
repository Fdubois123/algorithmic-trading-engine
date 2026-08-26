import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    BenchmarkComparison,
    annualized_standard_deviation,
    compare_to_benchmark,
    cumulative_return,
)


def returns(
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


def test_cumulative_return():
    result = cumulative_return(
        returns(
            [
                0.10,
                0.10,
            ]
        )
    )

    assert result == pytest.approx(0.21)


def test_annualized_standard_deviation():
    result = annualized_standard_deviation(
        returns(
            [
                0.01,
                -0.01,
                0.02,
            ]
        ),
        periods_per_year=252,
    )

    assert result > 0


def test_single_observation_volatility_is_zero():
    result = annualized_standard_deviation(returns([0.01]))

    assert result == 0.0


def test_compare_to_benchmark():
    portfolio = returns(
        [
            0.01,
            0.02,
            0.01,
        ]
    )

    benchmark = returns(
        [
            0.005,
            0.01,
            0.005,
        ]
    )

    result = compare_to_benchmark(
        portfolio,
        benchmark,
    )

    assert isinstance(
        result,
        BenchmarkComparison,
    )

    assert result.excess_total_return > 0


def test_identical_returns_have_zero_tracking_error():
    value = returns(
        [
            0.01,
            0.02,
            0.01,
        ]
    )

    result = compare_to_benchmark(
        value,
        value,
    )

    assert result.tracking_error == pytest.approx(0.0)

    assert result.information_ratio == pytest.approx(0.0)


def test_benchmark_indexes_must_match():
    portfolio = returns(
        [
            0.01,
            0.02,
        ]
    )

    benchmark = pd.Series(
        [
            0.01,
            0.02,
        ],
        index=pd.RangeIndex(2),
    )

    with pytest.raises(
        ValueError,
        match="matching indexes",
    ):
        compare_to_benchmark(
            portfolio,
            benchmark,
        )


def test_return_series_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        cumulative_return([0.01])


def test_empty_return_series_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        cumulative_return(pd.Series(dtype=float))


def test_non_finite_return_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        cumulative_return(
            returns(
                [
                    0.01,
                    np.inf,
                ]
            )
        )


@pytest.mark.parametrize(
    "periods",
    [
        True,
        252.5,
        "252",
    ],
)
def test_periods_per_year_requires_integer(
    periods,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        annualized_standard_deviation(
            returns(
                [
                    0.01,
                    0.02,
                ]
            ),
            periods_per_year=periods,
        )


def test_periods_per_year_must_be_positive():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        annualized_standard_deviation(
            returns(
                [
                    0.01,
                    0.02,
                ]
            ),
            periods_per_year=0,
        )
