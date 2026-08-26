import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    align_pair_prices,
    pair_log_returns,
    validate_price_series,
)


def prices(
    values,
    *,
    start="2026-01-01",
):
    return pd.Series(
        values,
        index=pd.date_range(
            start,
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def test_valid_price_series():
    series = prices([100, 101, 102])

    result = validate_price_series(series)

    assert np.allclose(
        result,
        series,
    )


def test_price_series_must_be_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        validate_price_series([100, 101])


def test_empty_price_series_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        validate_price_series(pd.Series(dtype=float))


def test_non_positive_price_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        validate_price_series(prices([100, 0, 102]))


def test_non_finite_price_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        validate_price_series(prices([100, np.inf, 102]))


def test_non_numeric_price_rejected():
    series = pd.Series(["a", "b", "c"])

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        validate_price_series(series)


def test_duplicate_index_rejected():
    index = pd.DatetimeIndex(
        [
            "2026-01-01",
            "2026-01-01",
        ]
    )

    series = pd.Series(
        [100.0, 101.0],
        index=index,
    )

    with pytest.raises(
        ValueError,
        match="duplicates",
    ):
        validate_price_series(series)


def test_unsorted_index_rejected():
    series = pd.Series(
        [100.0, 101.0],
        index=pd.DatetimeIndex(
            [
                "2026-01-02",
                "2026-01-01",
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match="sorted",
    ):
        validate_price_series(series)


def test_align_pair_uses_common_index():
    first = prices(
        [100, 101, 102],
        start="2026-01-01",
    )

    second = prices(
        [200, 201, 202],
        start="2026-01-02",
    )

    result = align_pair_prices(
        first,
        second,
    )

    assert len(result) == 2

    assert list(result.columns) == [
        "first",
        "second",
    ]


def test_alignment_requires_common_observations():
    first = prices(
        [100, 101],
        start="2026-01-01",
    )

    second = prices(
        [200, 201],
        start="2027-01-01",
    )

    with pytest.raises(
        ValueError,
        match="common observations",
    ):
        align_pair_prices(
            first,
            second,
        )


def test_pair_log_returns():
    first = prices([100, 110, 121])

    second = prices([200, 220, 242])

    result = pair_log_returns(
        first,
        second,
    )

    assert result.shape == (
        2,
        2,
    )

    assert np.allclose(
        result["first"],
        np.log(1.1),
    )

    assert np.allclose(
        result["second"],
        np.log(1.1),
    )
