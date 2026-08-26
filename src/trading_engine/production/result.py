from __future__ import annotations

from dataclasses import dataclass

from trading_engine.research import (
    ExperimentMetadata,
    ExperimentSummary,
    ResearchReport,
    ResearchResult,
)


@dataclass(slots=True, frozen=True)
class EngineResult:
    """Complete output of one production-engine run."""

    research: ResearchResult
    report: ResearchReport
    summary: ExperimentSummary
    metadata: ExperimentMetadata
    benchmark_name: str
    experiment_name: str

    @property
    def final_equity(self) -> float:
        return float(self.research.final_equity)

    @property
    def total_return(self) -> float:
        return float(self.research.total_return)

    @property
    def observations(self) -> int:
        return int(self.research.observations)

    @property
    def experiment_id(self) -> str:
        return self.metadata.experiment_id
