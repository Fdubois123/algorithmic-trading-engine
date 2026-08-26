import numpy as np
import pandas as pd
import pytest

from trading_engine.portfolio import (
    exponentially_weighted_covariance,
    sample_covariance,
    sample_expected_returns,
)


def returns_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AAPL": [
                0.01,
                -0.02,
                0.03,
                0.01,
            ],
            "MSFT": [
                0.02,
                0.01,
                -0.01,
                0.02,
            ],
            "GOOG": [
                -0.01,
                0.02,
                0.01,
                0.03,
            ],
        }
    )


def test_sample_expected_returns():
    frame = returns_frame()

    result = sample_expected_returns(
        frame,
        periods_per_year=252,
    )

    expected = frame.mean() * 252

    assert np.allclose(
        result.to_numpy(),
        expected.to_numpy(),
    )

    assert result.name == "expected_return"


def test_sample_covariance():
    frame = returns_frame()

    result = sample_covariance(
        frame,
        periods_per_year=252,
    )

    expected = frame.cov() * 252

    assert np.allclose(
        result.to_numpy(),
        expected.to_numpy(),
    )


def test_covariance_is_symmetric():
    result = sample_covariance(returns_frame())

    assert np.allclose(
        result.to_numpy(),
        result.to_numpy().T,
    )


def test_ewma_covariance_is_symmetric():
    result = exponentially_weighted_covariance(
        returns_frame(),
    )

    assert np.allclose(
        result.to_numpy(),
        result.to_numpy().T,
    )


def test_ewma_covariance_preserves_asset_labels():
    frame = returns_frame()

    result = exponentially_weighted_covariance(frame)

    assert list(result.columns) == [
        "AAPL",
        "MSFT",
        "GOOG",
    ]

    assert list(result.index) == [
        "AAPL",
        "MSFT",
        "GOOG",
    ]


def test_returns_must_be_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        sample_covariance([0.1, 0.2])


def test_empty_returns_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        sample_covariance(pd.DataFrame())


def test_one_observation_rejected():
    frame = pd.DataFrame(
        {
            "AAPL": [0.01],
            "MSFT": [0.02],
        }
    )

    with pytest.raises(
        ValueError,
        match="two observations",
    ):
        sample_covariance(frame)


def test_non_numeric_returns_rejected():
    frame = pd.DataFrame(
        {
            "AAPL": [
                "hello",
                "world",
            ]
        }
    )

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        sample_covariance(frame)


def test_non_finite_returns_rejected():
    frame = returns_frame()

    frame.loc[
        0,
        "AAPL",
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        sample_covariance(frame)


@pytest.mark.parametrize(
    "periods",
    [
        True,
        252.5,
        "252",
    ],
)
def test_invalid_period_type_rejected(
    periods,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        sample_expected_returns(
            returns_frame(),
            periods_per_year=periods,
        )


@pytest.mark.parametrize(
    "periods",
    [
        0,
        -1,
    ],
)
def test_non_positive_periods_rejected(
    periods,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        sample_covariance(
            returns_frame(),
            periods_per_year=periods,
        )


@pytest.mark.parametrize(
    "decay",
    [
        True,
        "0.94",
    ],
)
def test_invalid_decay_type_rejected(
    decay,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        exponentially_weighted_covariance(
            returns_frame(),
            decay=decay,
        )


@pytest.mark.parametrize(
    "decay",
    [
        0.0,
        1.0,
        -0.1,
        np.inf,
    ],
)
def test_invalid_decay_value_rejected(
    decay,
):
    with pytest.raises(ValueError):
        exponentially_weighted_covariance(
            returns_frame(),
            decay=decay,
        )
