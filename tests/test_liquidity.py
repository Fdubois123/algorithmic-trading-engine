import pytest

from trading_engine.execution import (
    ParticipationRateModel,
)


def test_maximum_quantity():
    model = ParticipationRateModel(
        max_participation_rate=0.10,
    )

    assert model.maximum_quantity(
        volume=100_000,
    ) == pytest.approx(10_000)


def test_small_order_fills_completely():
    model = ParticipationRateModel(
        max_participation_rate=0.10,
    )

    result = model.executable_quantity(
        requested_quantity=5_000,
        volume=100_000,
    )

    assert result == pytest.approx(5_000)


def test_large_order_is_partially_fillable():
    model = ParticipationRateModel(
        max_participation_rate=0.10,
    )

    result = model.executable_quantity(
        requested_quantity=25_000,
        volume=100_000,
    )

    assert result == pytest.approx(10_000)


@pytest.mark.parametrize(
    "rate",
    [0, -0.1, 1.1],
)
def test_invalid_participation_rate(rate):
    with pytest.raises(ValueError):
        ParticipationRateModel(
            max_participation_rate=rate,
        )


def test_zero_volume_is_rejected():
    model = ParticipationRateModel()

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        model.maximum_quantity(
            volume=0,
        )
