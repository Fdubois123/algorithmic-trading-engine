import numpy as np
import pytest

from trading_engine.portfolio import (
    validate_covariance_matrix,
    validate_expected_returns,
    validate_weights,
)


def test_valid_covariance():
    covariance = np.array(
        [
            [0.04, 0.01],
            [0.01, 0.09],
        ]
    )

    result = validate_covariance_matrix(covariance)

    assert np.array_equal(
        result,
        covariance,
    )


def test_covariance_must_be_two_dimensional():
    with pytest.raises(
        ValueError,
        match="two-dimensional",
    ):
        validate_covariance_matrix(np.array([0.1, 0.2]))


def test_covariance_must_be_square():
    with pytest.raises(
        ValueError,
        match="square",
    ):
        validate_covariance_matrix(np.ones((2, 3)))


def test_covariance_must_be_symmetric():
    with pytest.raises(
        ValueError,
        match="symmetric",
    ):
        validate_covariance_matrix(
            np.array(
                [
                    [1.0, 0.5],
                    [0.1, 1.0],
                ]
            )
        )


def test_covariance_rejects_negative_variance():
    with pytest.raises(
        ValueError,
        match="diagonal",
    ):
        validate_covariance_matrix(
            np.array(
                [
                    [-1.0, 0.0],
                    [0.0, 1.0],
                ]
            )
        )


def test_covariance_rejects_non_psd_matrix():
    with pytest.raises(
        ValueError,
        match="positive semidefinite",
    ):
        validate_covariance_matrix(
            np.array(
                [
                    [1.0, 2.0],
                    [2.0, 1.0],
                ]
            )
        )


def test_expected_returns_length_validation():
    with pytest.raises(
        ValueError,
        match="length",
    ):
        validate_expected_returns(
            np.array([0.1, 0.2]),
            number_of_assets=3,
        )


def test_weights_must_sum_to_one():
    with pytest.raises(
        ValueError,
        match="sum to 1",
    ):
        validate_weights(np.array([0.2, 0.2]))


def test_negative_weights_rejected_by_default():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        validate_weights(np.array([1.2, -0.2]))


def test_negative_weights_allowed_when_requested():
    result = validate_weights(
        np.array([1.2, -0.2]),
        allow_short=True,
    )

    assert np.allclose(
        result,
        [1.2, -0.2],
    )


def test_non_finite_weights_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        validate_weights(
            np.array([np.inf, -np.inf]),
            allow_short=True,
        )
