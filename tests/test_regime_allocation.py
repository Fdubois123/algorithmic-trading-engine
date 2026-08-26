import pytest

from trading_engine.regime import (
    MarketRegime,
    build_regime_allocation,
    normalize_strategy_weights,
    regime_gross_exposure,
    regime_strategy_preferences,
    validate_strategy_weights,
)


def test_validate_strategy_weights():
    result = validate_strategy_weights(
        {
            "trend": 0.5,
            "momentum": 0.5,
        }
    )

    assert result == {
        "trend": 0.5,
        "momentum": 0.5,
    }


def test_strategy_weights_require_mapping():
    with pytest.raises(
        TypeError,
        match="mapping",
    ):
        validate_strategy_weights([])


def test_empty_strategy_weights_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        validate_strategy_weights({})


def test_negative_strategy_weight_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        validate_strategy_weights(
            {
                "trend": -0.1,
                "momentum": 1.1,
            }
        )


def test_normalize_strategy_weights():
    result = normalize_strategy_weights(
        {
            "trend": 2.0,
            "momentum": 1.0,
        }
    )

    assert sum(result.values()) == pytest.approx(1.0)

    assert result["trend"] == pytest.approx(2 / 3)


@pytest.mark.parametrize(
    "regime",
    list(MarketRegime),
)
def test_every_regime_has_preferences(
    regime,
):
    result = regime_strategy_preferences(regime)

    assert sum(result.values()) == pytest.approx(1.0)

    assert all(value >= 0 for value in result.values())


def test_regime_preferences_require_enum():
    with pytest.raises(
        TypeError,
        match="MarketRegime",
    ):
        regime_strategy_preferences("high_vol_bear")


def test_high_vol_bear_reduces_exposure():
    defensive = regime_gross_exposure(
        MarketRegime.HIGH_VOL_BEAR,
        confidence=1.0,
    )

    bullish = regime_gross_exposure(
        MarketRegime.LOW_VOL_BULL,
        confidence=1.0,
    )

    assert defensive < bullish


def test_low_confidence_reduces_exposure():
    low_confidence = regime_gross_exposure(
        MarketRegime.LOW_VOL_BULL,
        confidence=0.0,
    )

    high_confidence = regime_gross_exposure(
        MarketRegime.LOW_VOL_BULL,
        confidence=1.0,
    )

    assert low_confidence < high_confidence


def test_confidence_above_one_rejected():
    with pytest.raises(
        ValueError,
        match="at most 1",
    ):
        regime_gross_exposure(
            MarketRegime.LOW_VOL_BULL,
            confidence=1.1,
        )


def test_invalid_exposure_bounds_rejected():
    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):
        regime_gross_exposure(
            MarketRegime.LOW_VOL_BULL,
            minimum_exposure=1.0,
            maximum_exposure=0.5,
        )


def test_build_regime_allocation():
    result = build_regime_allocation(
        MarketRegime.NORMAL_VOL_BULL,
        confidence=1.0,
    )

    assert result.gross_exposure == pytest.approx(sum(result.weights.values()))

    assert result.cash_weight == pytest.approx(1.0 - result.gross_exposure)

    assert result.invested_weight == pytest.approx(result.gross_exposure)


def test_high_vol_bear_has_cash_buffer():
    result = build_regime_allocation(
        MarketRegime.HIGH_VOL_BEAR,
        confidence=1.0,
    )

    assert result.cash_weight > 0
