import pytest

from trading_engine.regime import (
    AdaptiveAllocationResult,
    AdaptiveStrategyAllocator,
    MarketRegime,
    apply_strategy_turnover_limit,
    blend_with_base_allocation,
    strategy_turnover,
)


def test_strategy_turnover():
    result = strategy_turnover(
        {
            "trend": 0.5,
            "momentum": 0.5,
        },
        {
            "trend": 0.7,
            "momentum": 0.3,
        },
    )

    assert result == pytest.approx(0.2)


def test_turnover_supports_different_strategy_sets():
    result = strategy_turnover(
        {
            "trend": 1.0,
        },
        {
            "momentum": 1.0,
        },
    )

    assert result == pytest.approx(1.0)


def test_turnover_limit_returns_target_when_within_limit():
    target = {
        "trend": 0.6,
        "momentum": 0.4,
    }

    result = apply_strategy_turnover_limit(
        {
            "trend": 0.5,
            "momentum": 0.5,
        },
        target,
        maximum_turnover=0.2,
    )

    assert result == target


def test_turnover_limit_scales_large_change():
    current = {
        "trend": 1.0,
        "momentum": 0.0,
    }

    target = {
        "trend": 0.0,
        "momentum": 1.0,
    }

    result = apply_strategy_turnover_limit(
        current,
        target,
        maximum_turnover=0.25,
    )

    assert strategy_turnover(
        current,
        result,
    ) == pytest.approx(0.25)


def test_zero_turnover_preserves_current_allocation():
    current = {
        "trend": 1.0,
        "momentum": 0.0,
    }

    result = apply_strategy_turnover_limit(
        current,
        {
            "trend": 0.0,
            "momentum": 1.0,
        },
        maximum_turnover=0.0,
    )

    assert result == current


def test_negative_turnover_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        apply_strategy_turnover_limit(
            {
                "trend": 1.0,
            },
            {
                "trend": 1.0,
            },
            maximum_turnover=-1,
        )


def test_blending_with_zero_confidence_uses_base():
    base = {
        "trend": 0.8,
        "momentum": 0.2,
    }

    regime = {
        "trend": 0.1,
        "momentum": 0.9,
    }

    result = blend_with_base_allocation(
        regime,
        base,
        confidence=0.0,
    )

    assert result["trend"] == pytest.approx(0.8)

    assert result["momentum"] == pytest.approx(0.2)


def test_blending_with_full_confidence_uses_regime():
    result = blend_with_base_allocation(
        {
            "trend": 0.1,
            "momentum": 0.9,
        },
        {
            "trend": 0.8,
            "momentum": 0.2,
        },
        confidence=1.0,
    )

    assert result["momentum"] == pytest.approx(0.9)


def test_invalid_blend_confidence_rejected():
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        blend_with_base_allocation(
            {
                "trend": 1.0,
            },
            {
                "trend": 1.0,
            },
            confidence=2.0,
        )


def test_allocator_returns_result():
    allocator = AdaptiveStrategyAllocator()

    result = allocator.allocate(
        regime=MarketRegime.NORMAL_VOL_BULL,
        confidence=1.0,
    )

    assert isinstance(
        result,
        AdaptiveAllocationResult,
    )

    assert result.regime is (MarketRegime.NORMAL_VOL_BULL)

    assert result.gross_exposure > 0


def test_allocator_weights_do_not_exceed_maximum_exposure():
    allocator = AdaptiveStrategyAllocator(
        maximum_exposure=0.8,
        maximum_turnover=1.0,
    )

    result = allocator.allocate(
        regime=MarketRegime.LOW_VOL_BULL,
        confidence=1.0,
    )

    assert result.gross_exposure <= 0.8 + 1e-12


def test_allocator_applies_turnover_limit():
    allocator = AdaptiveStrategyAllocator(
        maximum_turnover=0.10,
    )

    first = allocator.allocate(
        regime=MarketRegime.LOW_VOL_BULL,
        confidence=1.0,
    )

    second = allocator.allocate(
        regime=MarketRegime.HIGH_VOL_BEAR,
        confidence=1.0,
    )

    assert first.turnover <= 0.10 + 1e-12
    assert second.turnover <= 0.10 + 1e-12


def test_allocator_reset():
    allocator = AdaptiveStrategyAllocator(
        maximum_turnover=1.0,
    )

    allocator.allocate(
        regime=MarketRegime.LOW_VOL_BULL,
        confidence=1.0,
    )

    allocator.reset()

    assert all(value == 0 for value in allocator.current_weights.values())


def test_allocator_rejects_invalid_regime():
    allocator = AdaptiveStrategyAllocator()

    with pytest.raises(
        TypeError,
        match="MarketRegime",
    ):
        allocator.allocate(
            regime="bull",
            confidence=1.0,
        )


@pytest.mark.parametrize(
    "confidence",
    [
        -0.1,
        1.1,
    ],
)
def test_allocator_rejects_invalid_confidence(
    confidence,
):
    allocator = AdaptiveStrategyAllocator()

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        allocator.allocate(
            regime=MarketRegime.NORMAL_VOL_BULL,
            confidence=confidence,
        )


def test_allocator_high_vol_bear_has_lower_exposure():
    defensive = AdaptiveStrategyAllocator(
        maximum_turnover=1.0,
    )

    bullish = AdaptiveStrategyAllocator(
        maximum_turnover=1.0,
    )

    defensive_result = defensive.allocate(
        regime=MarketRegime.HIGH_VOL_BEAR,
        confidence=1.0,
    )

    bullish_result = bullish.allocate(
        regime=MarketRegime.LOW_VOL_BULL,
        confidence=1.0,
    )

    assert defensive_result.gross_exposure < bullish_result.gross_exposure


def test_allocator_reports_cash_weight():
    allocator = AdaptiveStrategyAllocator(
        maximum_turnover=1.0,
    )

    result = allocator.allocate(
        regime=MarketRegime.HIGH_VOL_BEAR,
        confidence=1.0,
    )

    assert result.cash_weight == pytest.approx(1.0 - result.gross_exposure)
