import pytest

from trading_engine.execution import (
    FixedCommission,
    NoCommission,
    PercentageCommission,
    PerShareCommission,
)


def test_no_commission_returns_zero():
    model = NoCommission()

    assert model.calculate(
        quantity=100,
        price=50,
    ) == pytest.approx(0.0)


def test_fixed_commission():
    model = FixedCommission(
        amount=2.50,
    )

    assert model.calculate(
        quantity=100,
        price=50,
    ) == pytest.approx(2.50)


def test_percentage_commission():
    model = PercentageCommission(
        rate=0.001,
    )

    result = model.calculate(
        quantity=100,
        price=50,
    )

    assert result == pytest.approx(5.0)


def test_per_share_commission():
    model = PerShareCommission(
        per_share=0.01,
    )

    assert model.calculate(
        quantity=100,
        price=50,
    ) == pytest.approx(1.0)


def test_per_share_minimum_commission():
    model = PerShareCommission(
        per_share=0.001,
        minimum=1.0,
    )

    assert model.calculate(
        quantity=100,
        price=50,
    ) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "amount",
    [-1, -0.01],
)
def test_fixed_commission_rejects_negative_amount(
    amount,
):
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        FixedCommission(amount=amount)


@pytest.mark.parametrize(
    ("quantity", "price"),
    [
        (0, 100),
        (1, 0),
    ],
)
def test_commission_rejects_zero_execution_values(
    quantity,
    price,
):
    model = PercentageCommission()

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        model.calculate(
            quantity=quantity,
            price=price,
        )


@pytest.mark.parametrize(
    ("quantity", "price"),
    [
        (-1, 100),
        (1, -100),
    ],
)
def test_commission_rejects_negative_execution_values(
    quantity,
    price,
):
    model = PercentageCommission()

    with pytest.raises(
        ValueError,
        match="negative",
    ):
        model.calculate(
            quantity=quantity,
            price=price,
        )
