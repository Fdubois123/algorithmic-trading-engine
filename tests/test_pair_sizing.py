import pytest

from trading_engine.stat_arb import (
    PairLegWeights,
    PairPosition,
    pair_leg_weights,
    pair_share_quantities,
)


def test_flat_position_has_zero_weights():
    result = pair_leg_weights(
        hedge_ratio=2.0,
        position=PairPosition.FLAT,
    )

    assert result == PairLegWeights(
        dependent=0.0,
        independent=0.0,
    )


def test_long_spread_weights():
    result = pair_leg_weights(
        hedge_ratio=2.0,
        position=PairPosition.LONG_SPREAD,
    )

    assert result.dependent > 0
    assert result.independent < 0

    assert result.gross_exposure == pytest.approx(1.0)


def test_short_spread_weights():
    result = pair_leg_weights(
        hedge_ratio=2.0,
        position=PairPosition.SHORT_SPREAD,
    )

    assert result.dependent < 0
    assert result.independent > 0

    assert result.gross_exposure == pytest.approx(1.0)


def test_custom_gross_exposure():
    result = pair_leg_weights(
        hedge_ratio=1.5,
        position=PairPosition.LONG_SPREAD,
        gross_exposure=2.0,
    )

    assert result.gross_exposure == pytest.approx(2.0)


def test_zero_gross_exposure():
    result = pair_leg_weights(
        hedge_ratio=1.0,
        position=PairPosition.LONG_SPREAD,
        gross_exposure=0.0,
    )

    assert result.gross_exposure == 0.0


@pytest.mark.parametrize(
    "value",
    [
        True,
        "2",
    ],
)
def test_hedge_ratio_must_be_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        pair_leg_weights(
            hedge_ratio=value,
            position=PairPosition.FLAT,
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        float("inf"),
    ],
)
def test_hedge_ratio_must_be_positive_finite(
    value,
):
    with pytest.raises(ValueError):
        pair_leg_weights(
            hedge_ratio=value,
            position=PairPosition.FLAT,
        )


def test_position_must_be_pair_position():
    with pytest.raises(
        TypeError,
        match="PairPosition",
    ):
        pair_leg_weights(
            hedge_ratio=1.0,
            position="flat",
        )


def test_negative_gross_exposure_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        pair_leg_weights(
            hedge_ratio=1.0,
            position=PairPosition.FLAT,
            gross_exposure=-1.0,
        )


def test_pair_share_quantities_long_spread():
    dependent, independent = pair_share_quantities(
        capital=100_000,
        dependent_price=100,
        independent_price=50,
        hedge_ratio=1.0,
        position=PairPosition.LONG_SPREAD,
    )

    assert dependent == pytest.approx(500.0)

    assert independent == pytest.approx(-1000.0)


def test_pair_share_quantities_short_spread():
    dependent, independent = pair_share_quantities(
        capital=100_000,
        dependent_price=100,
        independent_price=50,
        hedge_ratio=1.0,
        position=PairPosition.SHORT_SPREAD,
    )

    assert dependent < 0
    assert independent > 0


@pytest.mark.parametrize(
    "name,value",
    [
        ("capital", True),
        ("capital", "100"),
        ("dependent_price", True),
        ("independent_price", "50"),
    ],
)
def test_share_inputs_must_be_numeric(
    name,
    value,
):
    kwargs = {
        "capital": 100_000,
        "dependent_price": 100,
        "independent_price": 50,
        "hedge_ratio": 1.0,
        "position": PairPosition.FLAT,
    }

    kwargs[name] = value

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        pair_share_quantities(**kwargs)


def test_negative_capital_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        pair_share_quantities(
            capital=-1,
            dependent_price=100,
            independent_price=50,
            hedge_ratio=1.0,
            position=PairPosition.FLAT,
        )


def test_zero_dependent_price_rejected():
    with pytest.raises(
        ValueError,
        match="dependent_price",
    ):
        pair_share_quantities(
            capital=100,
            dependent_price=0,
            independent_price=50,
            hedge_ratio=1.0,
            position=PairPosition.FLAT,
        )


def test_zero_independent_price_rejected():
    with pytest.raises(
        ValueError,
        match="independent_price",
    ):
        pair_share_quantities(
            capital=100,
            dependent_price=100,
            independent_price=0,
            hedge_ratio=1.0,
            position=PairPosition.FLAT,
        )
