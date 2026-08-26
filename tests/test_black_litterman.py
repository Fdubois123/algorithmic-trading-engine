import numpy as np
import pytest

from trading_engine.portfolio import (
    black_litterman_posterior,
    black_litterman_weights,
    default_view_uncertainty,
    market_implied_returns,
    validate_views,
)


def covariance() -> np.ndarray:
    return np.array(
        [
            [0.04, 0.01, 0.005],
            [0.01, 0.09, 0.010],
            [0.005, 0.010, 0.16],
        ]
    )


def market_weights() -> np.ndarray:
    return np.array([0.5, 0.3, 0.2])


def pick_matrix() -> np.ndarray:
    return np.array(
        [
            [1.0, -1.0, 0.0],
        ]
    )


def view_returns() -> np.ndarray:
    return np.array([0.03])


def test_market_implied_returns_shape():
    result = market_implied_returns(
        covariance(),
        market_weights(),
    )

    assert result.shape == (3,)


def test_market_implied_returns_formula():
    expected = 2.5 * covariance() @ market_weights()

    result = market_implied_returns(
        covariance(),
        market_weights(),
        risk_aversion=2.5,
    )

    assert np.allclose(
        result,
        expected,
    )


def test_view_validation():
    picks, views = validate_views(
        pick_matrix(),
        view_returns(),
        number_of_assets=3,
    )

    assert picks.shape == (1, 3)
    assert views.shape == (1,)


def test_view_column_count_must_match_assets():
    with pytest.raises(
        ValueError,
        match="columns",
    ):
        validate_views(
            np.array([[1.0, -1.0]]),
            view_returns(),
            number_of_assets=3,
        )


def test_zero_view_row_rejected():
    with pytest.raises(
        ValueError,
        match="at least one asset",
    ):
        validate_views(
            np.zeros((1, 3)),
            view_returns(),
            number_of_assets=3,
        )


def test_view_returns_length_must_match_views():
    with pytest.raises(
        ValueError,
        match="number of views",
    ):
        validate_views(
            np.array(
                [
                    [1.0, -1.0, 0.0],
                    [0.0, 1.0, -1.0],
                ]
            ),
            np.array([0.03]),
            number_of_assets=3,
        )


def test_default_omega_has_expected_shape():
    result = default_view_uncertainty(
        covariance(),
        pick_matrix(),
    )

    assert result.shape == (1, 1)
    assert result[0, 0] > 0


def test_posterior_shapes():
    posterior_return, posterior_covariance = black_litterman_posterior(
        covariance(),
        market_weights(),
        pick_matrix(),
        view_returns(),
    )

    assert posterior_return.shape == (3,)
    assert posterior_covariance.shape == (
        3,
        3,
    )


def test_posterior_covariance_is_symmetric():
    _, posterior_covariance = black_litterman_posterior(
        covariance(),
        market_weights(),
        pick_matrix(),
        view_returns(),
    )

    assert np.allclose(
        posterior_covariance,
        posterior_covariance.T,
    )


def test_positive_relative_view_moves_difference_up():
    equilibrium = market_implied_returns(
        covariance(),
        market_weights(),
    )

    posterior, _ = black_litterman_posterior(
        covariance(),
        market_weights(),
        pick_matrix(),
        np.array([0.10]),
    )

    prior_difference = equilibrium[0] - equilibrium[1]

    posterior_difference = posterior[0] - posterior[1]

    assert posterior_difference > prior_difference


def test_black_litterman_weights_sum_to_one():
    weights = black_litterman_weights(
        covariance(),
        market_weights(),
        pick_matrix(),
        view_returns(),
    )

    assert weights.sum() == pytest.approx(1.0)


def test_black_litterman_weights_are_long_only_by_default():
    weights = black_litterman_weights(
        covariance(),
        market_weights(),
        pick_matrix(),
        view_returns(),
    )

    assert np.all(weights >= 0)


@pytest.mark.parametrize(
    "risk_aversion",
    [
        0,
        -1,
        np.inf,
    ],
)
def test_invalid_risk_aversion_rejected(
    risk_aversion,
):
    with pytest.raises(ValueError):
        market_implied_returns(
            covariance(),
            market_weights(),
            risk_aversion=risk_aversion,
        )


@pytest.mark.parametrize(
    "tau",
    [
        0,
        -0.1,
        np.inf,
    ],
)
def test_invalid_tau_rejected(
    tau,
):
    with pytest.raises(ValueError):
        black_litterman_posterior(
            covariance(),
            market_weights(),
            pick_matrix(),
            view_returns(),
            tau=tau,
        )


def test_custom_omega_dimension_validation():
    with pytest.raises(
        ValueError,
        match="dimensions",
    ):
        black_litterman_posterior(
            covariance(),
            market_weights(),
            pick_matrix(),
            view_returns(),
            omega=np.eye(2),
        )


def test_non_positive_omega_diagonal_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        black_litterman_posterior(
            covariance(),
            market_weights(),
            pick_matrix(),
            view_returns(),
            omega=np.zeros((1, 1)),
        )
