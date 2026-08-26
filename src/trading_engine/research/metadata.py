from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from trading_engine.research.config import ResearchConfig


@dataclass(slots=True, frozen=True)
class ExperimentMetadata:
    """Reproducibility metadata for one research experiment."""

    experiment_id: str
    config_fingerprint: str
    created_at: str
    observations: int
    strategy_count: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalize_config_value(
    value: Any,
) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize_config_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (list, tuple)):
        return [_normalize_config_value(item) for item in value]

    return value


def config_fingerprint(
    config: ResearchConfig,
) -> str:
    """Return deterministic SHA-256 fingerprint for a research config."""
    if not isinstance(
        config,
        ResearchConfig,
    ):
        raise TypeError("config must be a ResearchConfig.")

    payload = {
        field: _normalize_config_value(value) for field, value in asdict(config).items()
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def experiment_identifier(
    *,
    config: ResearchConfig,
    observations: int,
    strategy_count: int,
) -> str:
    """Build deterministic experiment identity from config and dimensions."""
    if isinstance(
        observations,
        bool,
    ) or not isinstance(
        observations,
        int,
    ):
        raise TypeError("observations must be an integer.")

    if observations <= 0:
        raise ValueError("observations must be greater than zero.")

    if isinstance(
        strategy_count,
        bool,
    ) or not isinstance(
        strategy_count,
        int,
    ):
        raise TypeError("strategy_count must be an integer.")

    if strategy_count <= 0:
        raise ValueError("strategy_count must be greater than zero.")

    fingerprint = config_fingerprint(config)

    payload = f"{fingerprint}:{observations}:{strategy_count}"

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_experiment_metadata(
    *,
    config: ResearchConfig,
    observations: int,
    strategy_count: int,
    created_at: datetime | None = None,
) -> ExperimentMetadata:
    """Construct experiment metadata."""
    if created_at is None:
        created_at = datetime.now(UTC)

    if not isinstance(
        created_at,
        datetime,
    ):
        raise TypeError("created_at must be a datetime.")

    if created_at.tzinfo is None:
        raise ValueError("created_at must be timezone-aware.")

    fingerprint = config_fingerprint(config)

    identifier = experiment_identifier(
        config=config,
        observations=observations,
        strategy_count=strategy_count,
    )

    return ExperimentMetadata(
        experiment_id=identifier,
        config_fingerprint=fingerprint,
        created_at=created_at.astimezone(UTC).isoformat(),
        observations=observations,
        strategy_count=strategy_count,
    )
