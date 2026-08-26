import numpy as np
import pytest

from trading_engine.portfolio import (
    bounded_minimum_variance_weights,
    enforce_turnover_limit,
    portfolio_turnover,
    project_weights_to_bounded_simplex,
    validate_weight_bounds,
)


def covariance() -> np.ndarray:
    return np.array(
        [
            [0.04, 0.01, 0.00],
            [0.01, 0.09, 0.01],
            [0.00, 0.01, 0.16],
        ]
    )


def test_scalar_bounds_are_expanded():
    lower, upper = validate_weight_bounds(
        lower_bounds=0.0,
        upper_bounds=0.6,
        number_of_assets=3,
    )

    assert np.allclose(
        lower,
        [0.0, 0.0, 0.0],
    )

    assert np.allclose(
        upper,
        [0.6, 0.6, 0.6],
    )


def test_lower_bound_cannot_exceed_upper_bound():
    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):
        validate_weight_bounds(
            lower_bounds=np.array([0.7, 0.0]),
            upper_bounds=np.array([0.6, 1.0]),
            number_of_assets=2,
        )


def test_infeasible_lower_bounds_rejected():
    with pytest.raises(
        ValueError,
        match="infeasible",
    ):
        validate_weight_bounds(
            lower_bounds=0.6,
            upper_bounds=1.0,
            number_of_assets=2,
        )


def test_infeasible_upper_bounds_rejected():
    with pytest.raises(
        ValueError,
        match="infeasible",
    ):
        validate_weight_bounds(
            lower_bounds=0.0,
            upper_bounds=0.2,
            number_of_assets=3,
        )


def test_projection_sums_to_one():
    result = project_weights_to_bounded_simplex(np.array([0.8, 0.3, -0.1]))

    assert result.sum() == pytest.approx(1.0)


def test_projection_respects_bounds():
    result = project_weights_to_bounded_simplex(
        np.array([0.9, 0.05, 0.05]),
        lower_bounds=0.1,
        upper_bounds=0.6,
    )

    assert np.all(result >= 0.1 - 1e-10)

    assert np.all(result <= 0.6 + 1e-10)

    assert result.sum() == pytest.approx(1.0)


def test_portfolio_turnover():
    current = np.array([0.5, 0.5])

    target = np.array([0.7, 0.3])

    assert portfolio_turnover(
        current,
        target,
    ) == pytest.approx(0.2)


def test_turnover_limit_returns_target_when_within_budget():
    current = np.array([0.5, 0.5])

    target = np.array([0.6, 0.4])

    result = enforce_turnover_limit(
        current,
        target,
        max_turnover=0.2,
    )

    assert np.allclose(
        result,
        target,
    )


def test_turnover_limit_scales_rebalance():
    current = np.array([0.5, 0.5])

    target = np.array([1.0, 0.0])

    result = enforce_turnover_limit(
        current,
        target,
        max_turnover=0.1,
    )

    assert portfolio_turnover(
        current,
        result,
    ) == pytest.approx(0.1)


def test_zero_turnover_budget_preserves_current_weights():
    current = np.array([0.5, 0.5])

    target = np.array([1.0, 0.0])

    result = enforce_turnover_limit(
        current,
        target,
        max_turnover=0,
    )

    assert np.allclose(
        result,
        current,
    )


def test_bounded_minimum_variance_sums_to_one():
    result = bounded_minimum_variance_weights(
        covariance(),
    )

    assert result.sum() == pytest.approx(1.0)


def test_bounded_minimum_variance_respects_upper_bound():
    result = bounded_minimum_variance_weights(
        covariance(),
        upper_bounds=0.50,
    )

    assert np.all(result <= 0.5 + 1e-9)


def test_lower_variance_asset_receives_more_weight():
    result = bounded_minimum_variance_weights(np.diag([0.01, 0.04, 0.09]))

    assert result[0] > result[1]
    assert result[1] > result[2]


@pytest.mark.parametrize(
    "turnover",
    [
        "0.1",
        True,
    ],
)
def test_turnover_limit_rejects_non_numeric_budget(
    turnover,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        enforce_turnover_limit(
            np.array([0.5, 0.5]),
            np.array([0.6, 0.4]),
            max_turnover=turnover,
        )


def test_negative_turnover_budget_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        enforce_turnover_limit(
            np.array([0.5, 0.5]),
            np.array([0.6, 0.4]),
            max_turnover=-0.1,
        )
