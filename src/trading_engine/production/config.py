from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

from trading_engine.research.config import (
    ResearchConfig,
)


@dataclass(slots=True, frozen=True)
class EngineConfig:
    """Unified configuration for the production trading engine."""

    research: ResearchConfig = field(default_factory=ResearchConfig)

    initial_equity: float = 1_000_000.0
    periods_per_year: int = 252

    benchmark_name: str = "benchmark"
    experiment_name: str = "default"

    fail_on_missing_data: bool = True
    deterministic: bool = True

    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.research,
            ResearchConfig,
        ):
            raise TypeError("research must be a ResearchConfig.")

        if isinstance(
            self.initial_equity,
            bool,
        ) or not isinstance(
            self.initial_equity,
            (int, float),
        ):
            raise TypeError("initial_equity must be numeric.")

        initial_equity = float(self.initial_equity)

        if not math.isfinite(initial_equity):
            raise ValueError("initial_equity must be finite.")

        if initial_equity <= 0:
            raise ValueError("initial_equity must be greater than zero.")

        if isinstance(
            self.periods_per_year,
            bool,
        ) or not isinstance(
            self.periods_per_year,
            int,
        ):
            raise TypeError("periods_per_year must be an integer.")

        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be greater than zero.")

        for name in (
            "benchmark_name",
            "experiment_name",
        ):
            value = getattr(
                self,
                name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(f"{name} must be a string.")

            if not value.strip():
                raise ValueError(f"{name} cannot be empty.")

        if not isinstance(
            self.fail_on_missing_data,
            bool,
        ):
            raise TypeError("fail_on_missing_data must be a bool.")

        if not isinstance(
            self.deterministic,
            bool,
        ):
            raise TypeError("deterministic must be a bool.")

        if self.metadata is not None:
            if not isinstance(
                self.metadata,
                Mapping,
            ):
                raise TypeError("metadata must be a mapping.")

            for key, value in self.metadata.items():
                if not isinstance(
                    key,
                    str,
                ):
                    raise TypeError("metadata keys must be strings.")

                if not isinstance(
                    value,
                    str,
                ):
                    raise TypeError("metadata values must be strings.")

                if not key.strip():
                    raise ValueError("metadata keys cannot be empty.")

    @property
    def transaction_cost_bps(
        self,
    ) -> float:
        return float(self.research.transaction_cost_bps)

    @property
    def maximum_turnover(
        self,
    ) -> float:
        return float(self.research.maximum_turnover)

    @property
    def minimum_exposure(
        self,
    ) -> float:
        return float(self.research.minimum_exposure)

    @property
    def maximum_exposure(
        self,
    ) -> float:
        return float(self.research.maximum_exposure)

    def metadata_dict(
        self,
    ) -> dict[str, str]:
        if self.metadata is None:
            return {}

        return {str(key): str(value) for key, value in self.metadata.items()}
