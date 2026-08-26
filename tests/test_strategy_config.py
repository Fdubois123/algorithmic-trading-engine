import numpy as np
import pytest

from trading_engine.strategies.config import (
    StrategyConfig,
)


def test_default_configuration():
    config = StrategyConfig()

    assert config.allow_short is False
    assert config.max_position_weight == pytest.approx(1)
    assert config.signal_lag == 1


def test_shorting_can_be_enabled():
    config = StrategyConfig(
        allow_short=True,
    )

    assert config.allow_short is True


@pytest.mark.parametrize(
    "weight",
    [0, -0.1, 1.1],
)
def test_invalid_position_weight_is_rejected(weight):
    with pytest.raises(ValueError):
        StrategyConfig(
            max_position_weight=weight,
        )


@pytest.mark.parametrize(
    "threshold",
    [-0.1, 1.1],
)
def test_invalid_signal_threshold_is_rejected(
    threshold,
):
    with pytest.raises(ValueError):
        StrategyConfig(
            signal_threshold=threshold,
        )


@pytest.mark.parametrize(
    "field",
    [
        "minimum_holding_period",
        "cooldown_period",
        "signal_lag",
    ],
)
def test_negative_period_configuration_is_rejected(
    field,
):
    kwargs = {field: -1}

    with pytest.raises(ValueError, match="negative"):
        StrategyConfig(**kwargs)


def test_non_integer_signal_lag_is_rejected():
    with pytest.raises(TypeError, match="integer"):
        StrategyConfig(
            signal_lag=1.5,
        )


def test_non_finite_position_weight_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        StrategyConfig(
            max_position_weight=np.inf,
        )


def test_non_positive_gross_exposure_is_rejected():
    with pytest.raises(ValueError):
        StrategyConfig(
            max_gross_exposure=0,
        )
