from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from trading_engine.research.metadata import (
    ExperimentMetadata,
)
from trading_engine.research.reporting import (
    ResearchReport,
)
from trading_engine.research.result import (
    ResearchResult,
)


def _json_safe(
    value: Any,
) -> Any:
    if value is pd.NA:
        return None

    if isinstance(
        value,
        np.generic,
    ):
        return _json_safe(value.item())

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if isinstance(
        value,
        Path,
    ):
        return str(value)

    if isinstance(
        value,
        dict,
    ):
        return {str(key): _json_safe(item) for key, item in value.items()}

    if isinstance(
        value,
        (list, tuple),
    ):
        return [_json_safe(item) for item in value]

    if isinstance(
        value,
        float,
    ):
        if not math.isfinite(value):
            return None

        return value

    return value


def series_to_records(
    series: pd.Series,
) -> list[dict[str, object]]:
    """Serialize a Series into index/value records."""
    if not isinstance(
        series,
        pd.Series,
    ):
        raise TypeError("series must be a pandas Series.")

    return [
        {
            "index": _json_safe(index),
            "value": _json_safe(value),
        }
        for index, value in series.items()
    ]


def dataframe_to_records(
    frame: pd.DataFrame,
) -> list[dict[str, object]]:
    """Serialize a DataFrame into index + row records."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError("frame must be a pandas DataFrame.")

    records: list[dict[str, object]] = []

    for index, row in frame.iterrows():
        record = {
            "index": _json_safe(index),
        }

        for column, value in row.items():
            record[str(column)] = _json_safe(value)

        records.append(record)

    return records


def research_result_to_dict(
    result: ResearchResult,
) -> dict[str, object]:
    """Convert ResearchResult into a JSON-safe dictionary."""
    if not isinstance(
        result,
        ResearchResult,
    ):
        raise TypeError("result must be a ResearchResult.")

    return {
        "observations": result.observations,
        "final_equity": result.final_equity,
        "total_return": result.total_return,
        "total_transaction_cost": (result.total_transaction_cost),
        "average_turnover": (result.average_turnover),
        "equity_curve": series_to_records(result.equity_curve),
        "returns": series_to_records(result.returns),
        "gross_returns": series_to_records(result.gross_returns),
        "regime_frame": dataframe_to_records(result.regime_frame),
        "target_weights": dataframe_to_records(result.target_weights),
        "applied_weights": dataframe_to_records(result.applied_weights),
        "turnover": series_to_records(result.turnover),
        "transaction_costs": series_to_records(result.transaction_costs),
    }


def research_report_to_dict(
    report: ResearchReport,
) -> dict[str, object]:
    """Convert ResearchReport into a JSON-safe dictionary."""
    if not isinstance(
        report,
        ResearchReport,
    ):
        raise TypeError("report must be a ResearchReport.")

    return {
        "overview": {
            str(key): _json_safe(value) for key, value in report.overview.items()
        },
        "rolling_metrics": dataframe_to_records(report.rolling_metrics),
        "strategy_ranking": dataframe_to_records(report.strategy_ranking),
        "regime_ranking": dataframe_to_records(report.regime_ranking),
        "drawdown": {
            "maximum_drawdown": (report.drawdown.maximum_drawdown),
            "maximum_drawdown_duration": (report.drawdown.maximum_drawdown_duration),
            "current_drawdown": (report.drawdown.current_drawdown),
            "current_drawdown_duration": (report.drawdown.current_drawdown_duration),
        },
        "costs": {
            "total_cost": report.costs.total_cost,
            "average_cost": (report.costs.average_cost),
            "maximum_cost": (report.costs.maximum_cost),
            "total_turnover": (report.costs.total_turnover),
            "average_turnover": (report.costs.average_turnover),
            "cost_to_gross_return_ratio": (report.costs.cost_to_gross_return_ratio),
        },
    }


def export_research_bundle(
    *,
    path: str | Path,
    metadata: ExperimentMetadata,
    result: ResearchResult,
    report: ResearchReport | None = None,
) -> Path:
    """Export metadata, result and optional report to JSON."""
    if not isinstance(
        metadata,
        ExperimentMetadata,
    ):
        raise TypeError("metadata must be ExperimentMetadata.")

    destination = Path(path)

    if destination.exists() and destination.is_dir():
        raise ValueError("path must point to a file, not a directory.")

    if destination.suffix.lower() != ".json":
        raise ValueError("path must use a .json extension.")

    payload: dict[str, object] = {
        "metadata": metadata.as_dict(),
        "result": research_result_to_dict(result),
    }

    if report is not None:
        payload["report"] = research_report_to_dict(report)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_text(
        json.dumps(
            _json_safe(payload),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    return destination
