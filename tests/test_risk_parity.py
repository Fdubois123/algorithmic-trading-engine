import numpy as np
import pytest

from trading_engine.portfolio import (
    marginal_risk_contributions,
    percentage_risk_contributions,
    risk_contributions,
    risk_parity_weights,
)


def covariance() -> np.ndarray:
    return np.array(
        [
            [0.04, 0.006, 0.004],
            [0.006, 0.09, 0.010],
            [0.004, 0.010, 0.16],
        ]
    )


def test_marginal_risk_contributions_shape():
    result = marginal_risk_contributions(
        np.array([0.4, 0.3, 0.3]),
        covariance(),
    )

    assert result.shape == (3,)


def test_risk_contributions_sum_to_portfolio_volatility():
    weights = np.array([0.4, 0.3, 0.3])

    contributions = risk_contributions(
        weights,
        covariance(),
    )

    volatility = np.sqrt(weights @ covariance() @ weights)

    assert contributions.sum() == pytest.approx(volatility)


def test_percentage_contributions_sum_to_one():
    contributions = percentage_risk_contributions(
        np.array([0.4, 0.3, 0.3]),
        covariance(),
    )

    assert contributions.sum() == pytest.approx(1.0)


def test_risk_parity_weights_sum_to_one():
    weights = risk_parity_weights(covariance())

    assert weights.sum() == pytest.approx(1.0)


def test_risk_parity_weights_are_positive():
    weights = risk_parity_weights(covariance())

    assert np.all(weights > 0)


def test_risk_parity_equalizes_risk():
    weights = risk_parity_weights(
        covariance(),
        tolerance=1e-7,
    )

    contributions = percentage_risk_contributions(
        weights,
        covariance(),
    )

    assert np.allclose(
        contributions,
        np.full(
            3,
            1 / 3,
        ),
        atol=1e-6,
    )


def test_single_asset_risk_parity():
    weights = risk_parity_weights(np.array([[0.04]]))

    assert np.array_equal(
        weights,
        np.array([1.0]),
    )


def test_zero_covariance_uses_equal_weights():
    weights = risk_parity_weights(np.zeros((3, 3)))

    assert np.allclose(
        weights,
        np.full(
            3,
            1 / 3,
        ),
    )


@pytest.mark.parametrize(
    "tolerance",
    [
        True,
        "1e-8",
    ],
)
def test_invalid_tolerance_type_rejected(
    tolerance,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        risk_parity_weights(
            covariance(),
            tolerance=tolerance,
        )


@pytest.mark.parametrize(
    "tolerance",
    [
        0,
        -1,
        np.inf,
    ],
)
def test_invalid_tolerance_value_rejected(
    tolerance,
):
    with pytest.raises(ValueError):
        risk_parity_weights(
            covariance(),
            tolerance=tolerance,
        )


@pytest.mark.parametrize(
    "iterations",
    [
        True,
        1.5,
        "100",
    ],
)
def test_invalid_max_iterations_type_rejected(
    iterations,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        risk_parity_weights(
            covariance(),
            max_iterations=iterations,
        )


def test_non_positive_max_iterations_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        risk_parity_weights(
            covariance(),
            max_iterations=0,
        )


def test_non_convergence_raises_runtime_error():
    with pytest.raises(
        RuntimeError,
        match="failed to converge",
    ):
        risk_parity_weights(
            covariance(),
            tolerance=1e-15,
            max_iterations=1,
        )
