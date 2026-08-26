import numpy as np
import pandas as pd
import pytest

from trading_engine.portfolio import (
    black_litterman_posterior,
    bounded_minimum_variance_weights,
    diversification_gain,
    diversification_ratio,
    effective_number_of_assets,
    effective_number_of_risk_bets,
    exponentially_weighted_covariance,
    project_weights_to_bounded_simplex,
    risk_concentration,
    sample_covariance,
    sample_expected_returns,
    validate_covariance_matrix,
    validate_expected_returns,
    validate_views,
    validate_weight_bounds,
    validate_weights,
    weight_concentration,
)


def covariance() -> np.ndarray:
    return np.array(
        [
            [0.04, 0.01],
            [0.01, 0.09],
        ]
    )


def returns_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "A": [0.01, -0.02, 0.03],
            "B": [0.02, 0.01, -0.01],
        }
    )


# ---------------------------------------------------------------------------
# validation.py
# ---------------------------------------------------------------------------


def test_empty_covariance_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_covariance_matrix(np.empty((0, 0)))


def test_non_finite_covariance_is_rejected():
    matrix = np.array(
        [
            [1.0, 0.0],
            [0.0, np.inf],
        ]
    )

    with pytest.raises(ValueError, match="finite"):
        validate_covariance_matrix(matrix)


def test_expected_returns_must_be_one_dimensional():
    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        validate_expected_returns(np.ones((2, 2)))


def test_empty_expected_returns_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_expected_returns(np.array([]))


def test_non_finite_expected_returns_rejected():
    with pytest.raises(ValueError, match="finite"):
        validate_expected_returns(np.array([0.1, np.inf]))


def test_weights_must_be_one_dimensional():
    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        validate_weights(np.ones((2, 2)))


def test_empty_weights_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_weights(np.array([]))


def test_weight_length_mismatch_rejected():
    with pytest.raises(ValueError, match="length"):
        validate_weights(
            np.array([0.5, 0.5]),
            number_of_assets=3,
        )


def test_weights_can_skip_full_investment_requirement():
    result = validate_weights(
        np.array([0.2, 0.2]),
        require_fully_invested=False,
    )

    assert np.allclose(
        result,
        [0.2, 0.2],
    )


# ---------------------------------------------------------------------------
# estimation.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "periods",
    [
        True,
        252.5,
        "252",
    ],
)
def test_sample_covariance_rejects_invalid_period_type(
    periods,
):
    with pytest.raises(TypeError, match="integer"):
        sample_covariance(
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
def test_expected_returns_reject_non_positive_periods(
    periods,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        sample_expected_returns(
            returns_frame(),
            periods_per_year=periods,
        )


@pytest.mark.parametrize(
    "periods",
    [
        True,
        252.5,
        "252",
    ],
)
def test_ewma_rejects_invalid_period_type(
    periods,
):
    with pytest.raises(TypeError, match="integer"):
        exponentially_weighted_covariance(
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
def test_ewma_rejects_non_positive_periods(
    periods,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        exponentially_weighted_covariance(
            returns_frame(),
            periods_per_year=periods,
        )


# ---------------------------------------------------------------------------
# constraints.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "count",
    [
        True,
        2.5,
        "2",
    ],
)
def test_weight_bounds_require_integer_asset_count(
    count,
):
    with pytest.raises(TypeError, match="integer"):
        validate_weight_bounds(
            lower_bounds=0.0,
            upper_bounds=1.0,
            number_of_assets=count,
        )


def test_weight_bounds_require_positive_asset_count():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        validate_weight_bounds(
            lower_bounds=0.0,
            upper_bounds=1.0,
            number_of_assets=0,
        )


@pytest.mark.parametrize(
    "target",
    [
        True,
        "1",
    ],
)
def test_weight_bounds_require_numeric_target_sum(
    target,
):
    with pytest.raises(TypeError, match="numeric"):
        validate_weight_bounds(
            lower_bounds=0.0,
            upper_bounds=1.0,
            number_of_assets=2,
            target_sum=target,
        )


def test_weight_bounds_reject_non_finite_target():
    with pytest.raises(ValueError, match="finite"):
        validate_weight_bounds(
            lower_bounds=0.0,
            upper_bounds=1.0,
            number_of_assets=2,
            target_sum=np.inf,
        )


def test_bound_length_mismatch_rejected():
    with pytest.raises(ValueError, match="length"):
        validate_weight_bounds(
            lower_bounds=np.array([0.0]),
            upper_bounds=np.array([1.0, 1.0]),
            number_of_assets=2,
        )


def test_non_finite_bound_rejected():
    with pytest.raises(ValueError, match="finite"):
        validate_weight_bounds(
            lower_bounds=np.array([0.0, np.inf]),
            upper_bounds=np.array([1.0, 1.0]),
            number_of_assets=2,
        )


def test_projection_rejects_two_dimensional_weights():
    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        project_weights_to_bounded_simplex(np.ones((2, 2)))


def test_projection_rejects_empty_weights():
    with pytest.raises(ValueError, match="empty"):
        project_weights_to_bounded_simplex(np.array([]))


def test_projection_rejects_non_finite_weights():
    with pytest.raises(ValueError, match="finite"):
        project_weights_to_bounded_simplex(np.array([0.5, np.inf]))


@pytest.mark.parametrize(
    "tolerance",
    [
        True,
        "1e-8",
    ],
)
def test_projection_rejects_invalid_tolerance_type(
    tolerance,
):
    with pytest.raises(TypeError, match="numeric"):
        project_weights_to_bounded_simplex(
            np.array([0.5, 0.5]),
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
def test_projection_rejects_invalid_tolerance_value(
    tolerance,
):
    with pytest.raises(ValueError):
        project_weights_to_bounded_simplex(
            np.array([0.5, 0.5]),
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
def test_projection_rejects_invalid_iteration_type(
    iterations,
):
    with pytest.raises(TypeError, match="integer"):
        project_weights_to_bounded_simplex(
            np.array([0.5, 0.5]),
            max_iterations=iterations,
        )


def test_projection_rejects_non_positive_iterations():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        project_weights_to_bounded_simplex(
            np.array([0.5, 0.5]),
            max_iterations=0,
        )


@pytest.mark.parametrize(
    "tolerance",
    [
        True,
        "1e-8",
    ],
)
def test_bounded_min_variance_rejects_invalid_tolerance_type(
    tolerance,
):
    with pytest.raises(TypeError, match="numeric"):
        bounded_minimum_variance_weights(
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
def test_bounded_min_variance_rejects_invalid_tolerance(
    tolerance,
):
    with pytest.raises(ValueError):
        bounded_minimum_variance_weights(
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
def test_bounded_min_variance_rejects_invalid_iteration_type(
    iterations,
):
    with pytest.raises(TypeError, match="integer"):
        bounded_minimum_variance_weights(
            covariance(),
            max_iterations=iterations,
        )


def test_bounded_min_variance_rejects_zero_iterations():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        bounded_minimum_variance_weights(
            covariance(),
            max_iterations=0,
        )


def test_zero_covariance_returns_feasible_allocation():
    result = bounded_minimum_variance_weights(
        np.zeros((2, 2)),
    )

    assert result.sum() == pytest.approx(1.0)
    assert np.all(result >= 0)


# ---------------------------------------------------------------------------
# metrics.py
# ---------------------------------------------------------------------------


def test_effective_assets_for_single_asset():
    assert effective_number_of_assets(np.array([1.0])) == pytest.approx(1.0)


def test_zero_variance_diversification_ratio_is_zero():
    result = diversification_ratio(
        np.array([0.5, 0.5]),
        np.zeros((2, 2)),
    )

    assert result == pytest.approx(0.0)


def test_zero_risk_effective_bets_is_zero():
    result = effective_number_of_risk_bets(
        np.array([0.5, 0.5]),
        np.zeros((2, 2)),
    )

    assert result == pytest.approx(0.0)


def test_zero_risk_concentration_is_zero():
    result = risk_concentration(
        np.array([0.5, 0.5]),
        np.zeros((2, 2)),
    )

    assert result == pytest.approx(0.0)


def test_zero_covariance_diversification_gain_is_zero():
    result = diversification_gain(
        np.array([0.5, 0.5]),
        np.zeros((2, 2)),
    )

    assert result == pytest.approx(0.0)


def test_weight_concentration_rejects_short_weights():
    with pytest.raises(ValueError, match="negative"):
        weight_concentration(np.array([1.2, -0.2]))


# ---------------------------------------------------------------------------
# black_litterman.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "risk_aversion",
    [
        True,
        "2.5",
    ],
)
def test_market_implied_returns_reject_invalid_risk_aversion_type(
    risk_aversion,
):
    from trading_engine.portfolio import (
        market_implied_returns,
    )

    with pytest.raises(TypeError, match="numeric"):
        market_implied_returns(
            covariance(),
            np.array([0.5, 0.5]),
            risk_aversion=risk_aversion,
        )


def test_pick_matrix_must_be_two_dimensional():
    with pytest.raises(
        ValueError,
        match="two-dimensional",
    ):
        validate_views(
            np.array([1.0, -1.0]),
            np.array([0.03]),
            number_of_assets=2,
        )


def test_empty_pick_matrix_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_views(
            np.empty((0, 2)),
            np.array([]),
            number_of_assets=2,
        )


def test_non_finite_pick_matrix_rejected():
    with pytest.raises(ValueError, match="finite"):
        validate_views(
            np.array(
                [
                    [1.0, np.inf],
                ]
            ),
            np.array([0.03]),
            number_of_assets=2,
        )


def test_valid_custom_omega_executes():
    posterior_returns, posterior_covariance = black_litterman_posterior(
        covariance(),
        np.array([0.5, 0.5]),
        np.array(
            [
                [1.0, -1.0],
            ]
        ),
        np.array([0.03]),
        omega=np.array(
            [
                [0.01],
            ]
        ),
    )

    assert posterior_returns.shape == (2,)
    assert posterior_covariance.shape == (2, 2)
