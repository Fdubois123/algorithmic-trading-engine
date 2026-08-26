import numpy as np
import pytest

from trading_engine.portfolio import (
    equal_weight_portfolio,
    maximum_sharpe_weights,
    minimum_variance_weights,
    portfolio_return,
    portfolio_variance,
    portfolio_volatility,
)


def covariance() -> np.ndarray:
    return np.array(
        [
            [0.04, 0.006],
            [0.006, 0.09],
        ]
    )


def test_equal_weight_portfolio():
    weights = equal_weight_portfolio(4)

    assert np.allclose(
        weights,
        [0.25, 0.25, 0.25, 0.25],
    )


@pytest.mark.parametrize(
    "count",
    [
        True,
        2.5,
        "2",
    ],
)
def test_equal_weight_requires_integer(
    count,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        equal_weight_portfolio(count)


def test_equal_weight_requires_positive_count():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        equal_weight_portfolio(0)


def test_portfolio_return():
    result = portfolio_return(
        np.array([0.5, 0.5]),
        np.array([0.10, 0.20]),
    )

    assert result == pytest.approx(0.15)


def test_portfolio_variance():
    weights = np.array([0.5, 0.5])

    expected = float(weights @ covariance() @ weights)

    result = portfolio_variance(
        weights,
        covariance(),
    )

    assert result == pytest.approx(expected)


def test_portfolio_volatility():
    variance = portfolio_variance(
        np.array([0.5, 0.5]),
        covariance(),
    )

    volatility = portfolio_volatility(
        np.array([0.5, 0.5]),
        covariance(),
    )

    assert volatility == pytest.approx(np.sqrt(variance))


def test_minimum_variance_weights_sum_to_one():
    weights = minimum_variance_weights(covariance())

    assert weights.sum() == pytest.approx(1.0)


def test_minimum_variance_weights_are_long_only():
    weights = minimum_variance_weights(
        covariance(),
        allow_short=False,
    )

    assert np.all(weights >= 0)


def test_lower_variance_asset_gets_larger_weight():
    weights = minimum_variance_weights(
        np.array(
            [
                [0.01, 0.0],
                [0.0, 0.09],
            ]
        )
    )

    assert weights[0] > weights[1]


def test_maximum_sharpe_weights_sum_to_one():
    weights = maximum_sharpe_weights(
        np.array([0.10, 0.16]),
        covariance(),
    )

    assert weights.sum() == pytest.approx(1.0)


def test_maximum_sharpe_is_long_only_by_default():
    weights = maximum_sharpe_weights(
        np.array([0.10, 0.16]),
        covariance(),
    )

    assert np.all(weights >= 0)


def test_maximum_sharpe_rejects_invalid_return_length():
    with pytest.raises(
        ValueError,
        match="length",
    ):
        maximum_sharpe_weights(
            np.array([0.10]),
            covariance(),
        )


@pytest.mark.parametrize(
    "risk_free",
    [
        True,
        "0.02",
    ],
)
def test_maximum_sharpe_rejects_invalid_risk_free_type(
    risk_free,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        maximum_sharpe_weights(
            np.array([0.10, 0.16]),
            covariance(),
            risk_free_rate=risk_free,
        )


def test_maximum_sharpe_rejects_non_finite_risk_free_rate():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        maximum_sharpe_weights(
            np.array([0.10, 0.16]),
            covariance(),
            risk_free_rate=np.inf,
        )


def test_maximum_sharpe_fails_when_no_positive_long_only_solution():
    with pytest.raises(
        ValueError,
        match="cannot be determined",
    ):
        maximum_sharpe_weights(
            np.array([-0.10, -0.20]),
            covariance(),
            risk_free_rate=0.0,
            allow_short=False,
        )
