from datetime import UTC, datetime, timedelta, timezone

import pytest

from trading_engine.research import (
    ExperimentMetadata,
    ResearchConfig,
    build_experiment_metadata,
    config_fingerprint,
    experiment_identifier,
)


def test_config_fingerprint_is_deterministic():
    config = ResearchConfig()

    first = config_fingerprint(config)

    second = config_fingerprint(config)

    assert first == second
    assert len(first) == 64


def test_different_configs_have_different_fingerprints():
    first = config_fingerprint(ResearchConfig())

    second = config_fingerprint(
        ResearchConfig(
            maximum_turnover=0.5,
        )
    )

    assert first != second


def test_fingerprint_requires_config():
    with pytest.raises(
        TypeError,
        match="ResearchConfig",
    ):
        config_fingerprint("bad")


def test_experiment_identifier_is_deterministic():
    config = ResearchConfig()

    first = experiment_identifier(
        config=config,
        observations=100,
        strategy_count=5,
    )

    second = experiment_identifier(
        config=config,
        observations=100,
        strategy_count=5,
    )

    assert first == second
    assert len(first) == 64


@pytest.mark.parametrize(
    "value",
    [
        True,
        1.5,
        "100",
    ],
)
def test_observations_requires_integer(
    value,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        experiment_identifier(
            config=ResearchConfig(),
            observations=value,
            strategy_count=5,
        )


def test_observations_must_be_positive():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        experiment_identifier(
            config=ResearchConfig(),
            observations=0,
            strategy_count=5,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        1.5,
        "5",
    ],
)
def test_strategy_count_requires_integer(
    value,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        experiment_identifier(
            config=ResearchConfig(),
            observations=100,
            strategy_count=value,
        )


def test_strategy_count_must_be_positive():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        experiment_identifier(
            config=ResearchConfig(),
            observations=100,
            strategy_count=0,
        )


def test_build_metadata():
    timestamp = datetime(
        2026,
        8,
        26,
        10,
        0,
        tzinfo=UTC,
    )

    result = build_experiment_metadata(
        config=ResearchConfig(),
        observations=100,
        strategy_count=5,
        created_at=timestamp,
    )

    assert isinstance(
        result,
        ExperimentMetadata,
    )

    assert result.observations == 100
    assert result.strategy_count == 5

    assert result.created_at == timestamp.isoformat()

    assert len(result.experiment_id) == 64

    assert len(result.config_fingerprint) == 64


def test_metadata_as_dict():
    result = build_experiment_metadata(
        config=ResearchConfig(),
        observations=100,
        strategy_count=5,
    )

    payload = result.as_dict()

    assert payload["experiment_id"] == result.experiment_id

    assert payload["config_fingerprint"] == result.config_fingerprint

    assert payload["created_at"] == result.created_at

    assert payload["observations"] == 100
    assert payload["strategy_count"] == 5


def test_created_at_requires_datetime():
    with pytest.raises(
        TypeError,
        match="datetime",
    ):
        build_experiment_metadata(
            config=ResearchConfig(),
            observations=100,
            strategy_count=5,
            created_at="now",
        )


def test_created_at_requires_timezone():
    aware_timestamp = datetime(
        2026,
        8,
        26,
        tzinfo=UTC,
    )

    naive_timestamp = aware_timestamp.replace(tzinfo=None)

    assert naive_timestamp.tzinfo is None

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        build_experiment_metadata(
            config=ResearchConfig(),
            observations=100,
            strategy_count=5,
            created_at=naive_timestamp,
        )


def test_created_at_is_normalized_to_utc():
    india_timezone = timezone(
        timedelta(
            hours=5,
            minutes=30,
        )
    )

    timestamp = datetime(
        2026,
        8,
        26,
        15,
        30,
        tzinfo=india_timezone,
    )

    result = build_experiment_metadata(
        config=ResearchConfig(),
        observations=100,
        strategy_count=5,
        created_at=timestamp,
    )

    expected = datetime(
        2026,
        8,
        26,
        10,
        0,
        tzinfo=UTC,
    )

    assert result.created_at == expected.isoformat()


def test_metadata_experiment_id_changes_with_observations():
    config = ResearchConfig()

    first = build_experiment_metadata(
        config=config,
        observations=100,
        strategy_count=5,
    )

    second = build_experiment_metadata(
        config=config,
        observations=200,
        strategy_count=5,
    )

    assert first.experiment_id != second.experiment_id


def test_metadata_experiment_id_changes_with_strategy_count():
    config = ResearchConfig()

    first = build_experiment_metadata(
        config=config,
        observations=100,
        strategy_count=5,
    )

    second = build_experiment_metadata(
        config=config,
        observations=100,
        strategy_count=4,
    )

    assert first.experiment_id != second.experiment_id


def test_metadata_config_fingerprint_matches_direct_fingerprint():
    config = ResearchConfig(
        volatility_window=10,
        trend_window=30,
        maximum_turnover=0.4,
    )

    metadata = build_experiment_metadata(
        config=config,
        observations=100,
        strategy_count=5,
    )

    assert metadata.config_fingerprint == config_fingerprint(config)


def test_experiment_identifier_changes_with_config():
    first = experiment_identifier(
        config=ResearchConfig(),
        observations=100,
        strategy_count=5,
    )

    second = experiment_identifier(
        config=ResearchConfig(
            maximum_turnover=0.6,
        ),
        observations=100,
        strategy_count=5,
    )

    assert first != second
