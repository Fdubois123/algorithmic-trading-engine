import numpy as np
import pytest

from trading_engine.portfolio import (
    diversification_gain,
    diversification_ratio,
    effective_number_of_assets,
    effective_number_of_risk_bets,
    risk_concentration,
    weight_concentration,
)


def covariance() -> np.ndarray:
    return np.array(
        [
            [0.04, 0.01],
            [0.01, 0.09],
        ]
    )


def test_equal_weights_have_expected_concentration():
    result = weight_concentration(np.array([0.5, 0.5]))

    assert result == pytest.approx(0.5)


def test_single_asset_has_maximum_concentration():
    result = weight_concentration(np.array([1.0, 0.0]))

    assert result == pytest.approx(1.0)


def test_effective_number_of_assets():
    result = effective_number_of_assets(np.array([0.5, 0.5]))

    assert result == pytest.approx(2.0)


def test_diversification_ratio_is_at_least_one():
    result = diversification_ratio(
        np.array([0.5, 0.5]),
        covariance(),
    )

    assert result >= 1.0


def test_diversification_gain_is_non_negative():
    result = diversification_gain(
        np.array([0.5, 0.5]),
        covariance(),
    )

    assert result >= 0.0


def test_risk_concentration_is_bounded():
    result = risk_concentration(
        np.array([0.5, 0.5]),
        covariance(),
    )

    assert 0 < result <= 1


def test_effective_number_of_risk_bets_is_positive():
    result = effective_number_of_risk_bets(
        np.array([0.5, 0.5]),
        covariance(),
    )

    assert result > 0


def test_more_balanced_weights_have_more_effective_assets():
    concentrated = effective_number_of_assets(np.array([0.9, 0.1]))

    balanced = effective_number_of_assets(np.array([0.5, 0.5]))

    assert balanced > concentrated
