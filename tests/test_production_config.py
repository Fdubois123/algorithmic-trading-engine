import pytest

from trading_engine.production import (
    EngineConfig,
)
from trading_engine.research import (
    ResearchConfig,
)


def test_default_engine_config():
    config = EngineConfig()

    assert isinstance(
        config.research,
        ResearchConfig,
    )

    assert config.initial_equity == pytest.approx(1_000_000.0)

    assert config.periods_per_year == 252
    assert config.fail_on_missing_data
    assert config.deterministic


def test_custom_research_config():
    research = ResearchConfig(
        transaction_cost_bps=12.5,
        maximum_turnover=0.4,
        minimum_exposure=0.2,
        maximum_exposure=0.9,
    )

    config = EngineConfig(research=research)

    assert config.transaction_cost_bps == pytest.approx(12.5)

    assert config.maximum_turnover == pytest.approx(0.4)

    assert config.minimum_exposure == pytest.approx(0.2)

    assert config.maximum_exposure == pytest.approx(0.9)


def test_research_must_be_research_config():
    with pytest.raises(
        TypeError,
        match="ResearchConfig",
    ):
        EngineConfig(research="bad")


@pytest.mark.parametrize(
    "value",
    [
        True,
        "1000000",
    ],
)
def test_initial_equity_requires_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        EngineConfig(initial_equity=value)


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        -1.0,
    ],
)
def test_initial_equity_must_be_positive(
    value,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        EngineConfig(initial_equity=value)


def test_initial_equity_must_be_finite():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        EngineConfig(initial_equity=float("inf"))


@pytest.mark.parametrize(
    "value",
    [
        True,
        252.5,
        "252",
    ],
)
def test_periods_per_year_requires_integer(
    value,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        EngineConfig(periods_per_year=value)


def test_periods_per_year_must_be_positive():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        EngineConfig(periods_per_year=0)


@pytest.mark.parametrize(
    "field",
    [
        "benchmark_name",
        "experiment_name",
    ],
)
def test_names_require_strings(
    field,
):
    with pytest.raises(
        TypeError,
        match="string",
    ):
        EngineConfig(
            **{
                field: 123,
            }
        )


@pytest.mark.parametrize(
    "field",
    [
        "benchmark_name",
        "experiment_name",
    ],
)
def test_names_cannot_be_empty(
    field,
):
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        EngineConfig(
            **{
                field: "   ",
            }
        )


def test_fail_on_missing_data_requires_bool():
    with pytest.raises(
        TypeError,
        match="bool",
    ):
        EngineConfig(fail_on_missing_data=1)


def test_deterministic_requires_bool():
    with pytest.raises(
        TypeError,
        match="bool",
    ):
        EngineConfig(deterministic=1)


def test_metadata_defaults_to_empty_dict():
    config = EngineConfig()

    assert config.metadata_dict() == {}


def test_metadata_round_trip():
    config = EngineConfig(
        metadata={
            "owner": "quant-team",
            "environment": "research",
        }
    )

    assert config.metadata_dict() == {
        "owner": "quant-team",
        "environment": "research",
    }


def test_metadata_requires_mapping():
    with pytest.raises(
        TypeError,
        match="mapping",
    ):
        EngineConfig(metadata=["bad"])


def test_metadata_keys_must_be_strings():
    with pytest.raises(
        TypeError,
        match="keys",
    ):
        EngineConfig(
            metadata={
                1: "value",
            }
        )


def test_metadata_values_must_be_strings():
    with pytest.raises(
        TypeError,
        match="values",
    ):
        EngineConfig(
            metadata={
                "owner": 123,
            }
        )


def test_metadata_keys_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        EngineConfig(
            metadata={
                "   ": "value",
            }
        )
