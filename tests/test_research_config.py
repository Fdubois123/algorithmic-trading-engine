import pytest

from trading_engine.research import (
    ResearchConfig,
)


def test_default_config():
    config = ResearchConfig()

    assert config.volatility_window == 20
    assert config.trend_window == 50
    assert config.maximum_exposure == 1.0


@pytest.mark.parametrize(
    "field",
    [
        "volatility_window",
        "trend_window",
        "momentum_lookback",
    ],
)
def test_integer_fields_reject_bool(
    field,
):
    kwargs = {
        field: True,
    }

    with pytest.raises(
        TypeError,
        match="integer",
    ):
        ResearchConfig(**kwargs)


def test_volatility_window_minimum():
    with pytest.raises(
        ValueError,
        match="at least 2",
    ):
        ResearchConfig(
            volatility_window=1,
        )


def test_trend_window_minimum():
    with pytest.raises(
        ValueError,
        match="at least 2",
    ):
        ResearchConfig(
            trend_window=1,
        )


def test_invalid_quantiles_rejected():
    with pytest.raises(
        ValueError,
        match="quantiles",
    ):
        ResearchConfig(
            low_volatility_quantile=0.8,
            high_volatility_quantile=0.2,
        )


def test_negative_transaction_cost_rejected():
    with pytest.raises(
        ValueError,
        match="transaction_cost_bps",
    ):
        ResearchConfig(
            transaction_cost_bps=-1.0,
        )


def test_exposure_bounds_validation():
    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):
        ResearchConfig(
            minimum_exposure=1.0,
            maximum_exposure=0.5,
        )


def test_negative_turnover_rejected():
    with pytest.raises(
        ValueError,
        match="maximum_turnover",
    ):
        ResearchConfig(
            maximum_turnover=-0.1,
        )
