from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from trading_engine.production.result import (
    EngineResult,
)
from trading_engine.research.serialization import (
    research_report_to_dict,
    research_result_to_dict,
)


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def _write_json(
    path: Path,
    payload: object,
) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )


def _summary_to_dict(
    result: EngineResult,
) -> dict[str, object]:
    summary = result.summary

    benchmark = None

    if summary.benchmark is not None:
        benchmark = asdict(summary.benchmark)

    return {
        "final_equity": (summary.final_equity),
        "total_return": (summary.total_return),
        "total_transaction_cost": (summary.total_transaction_cost),
        "average_turnover": (summary.average_turnover),
        "benchmark": benchmark,
        "strategy_contributions": {
            str(key): float(value)
            for key, value in summary.strategy_contributions.items()
        },
        "regime_performance": (summary.regime_performance.to_dict(orient="records")),
    }


def experiment_directory(
    *,
    root: str | Path,
    result: EngineResult,
) -> Path:
    """Return deterministic directory for an engine result."""
    if not isinstance(
        result,
        EngineResult,
    ):
        raise TypeError("result must be an EngineResult.")

    root_path = Path(root)

    return root_path / result.experiment_id


def persist_engine_result(
    *,
    root: str | Path,
    result: EngineResult,
    overwrite: bool = False,
) -> Path:
    """Persist a complete engine result into a deterministic directory."""
    if not isinstance(
        result,
        EngineResult,
    ):
        raise TypeError("result must be an EngineResult.")

    if not isinstance(
        overwrite,
        bool,
    ):
        raise TypeError("overwrite must be a bool.")

    destination = experiment_directory(
        root=root,
        result=result,
    )

    if destination.exists():
        if not overwrite:
            raise FileExistsError("experiment directory already exists.")

        if not destination.is_dir():
            raise ValueError("experiment path exists and is not a directory.")

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path = destination / "metadata.json"

    result_path = destination / "result.json"

    report_path = destination / "report.json"

    summary_path = destination / "summary.json"

    manifest_path = destination / "manifest.json"

    _write_json(
        metadata_path,
        result.metadata.as_dict(),
    )

    _write_json(
        result_path,
        research_result_to_dict(result.research),
    )

    _write_json(
        report_path,
        research_report_to_dict(result.report),
    )

    _write_json(
        summary_path,
        _summary_to_dict(result),
    )

    manifest = {
        "experiment_id": (result.experiment_id),
        "benchmark_name": (result.benchmark_name),
        "experiment_name": (result.experiment_name),
        "files": {
            "metadata.json": _sha256_file(metadata_path),
            "result.json": _sha256_file(result_path),
            "report.json": _sha256_file(report_path),
            "summary.json": _sha256_file(summary_path),
        },
    }

    _write_json(
        manifest_path,
        manifest,
    )

    return destination


def load_manifest(
    path: str | Path,
) -> dict[str, object]:
    """Load an artifact manifest from an experiment directory."""
    directory = Path(path)

    if not directory.exists():
        raise FileNotFoundError("experiment directory does not exist.")

    if not directory.is_dir():
        raise ValueError("path must point to an experiment directory.")

    manifest_path = directory / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError("manifest.json is missing.")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("manifest.json is not valid JSON.") from error

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError("manifest.json must contain a JSON object.")

    return payload


def verify_experiment_artifacts(
    path: str | Path,
) -> bool:
    """Verify experiment files against the stored SHA-256 manifest."""
    directory = Path(path)

    manifest = load_manifest(directory)

    files = manifest.get("files")

    if not isinstance(
        files,
        dict,
    ):
        raise TypeError("manifest files section is invalid.")

    required = {
        "metadata.json",
        "result.json",
        "report.json",
        "summary.json",
    }

    if set(files) != required:
        raise ValueError("manifest files section is incomplete.")

    for name in sorted(required):
        expected = files[name]

        if not isinstance(
            expected,
            str,
        ):
            raise TypeError("manifest checksum values must be strings.")

        file_path = directory / name

        if not file_path.exists():
            return False

        actual = _sha256_file(file_path)

        if actual != expected:
            return False

    return True
