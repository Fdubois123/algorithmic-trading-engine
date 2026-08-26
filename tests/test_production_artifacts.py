import json

import numpy as np
import pandas as pd
import pytest

from trading_engine.production import (
    EngineConfig,
    experiment_directory,
    load_manifest,
    persist_engine_result,
    run_engine,
    verify_experiment_artifacts,
)
from trading_engine.research import (
    ResearchConfig,
)


def prices(
    observations: int = 80,
) -> pd.Series:
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    values = np.linspace(
        100.0,
        130.0,
        observations,
    ) + np.sin(np.arange(observations) / 4.0)

    return pd.Series(
        values,
        index=index,
        dtype=float,
    )


def strategy_returns(
    index: pd.Index,
) -> pd.DataFrame:
    x = np.arange(
        len(index),
        dtype=float,
    )

    return pd.DataFrame(
        {
            "trend": (np.sin(x / 6.0) * 0.01),
            "momentum": (np.cos(x / 8.0) * 0.01),
            "mean_reversion": (-np.sin(x / 5.0) * 0.008),
            "volatility": (np.sin(x / 3.0) * 0.005),
            "stat_arb": (np.cos(x / 4.0) * 0.006),
        },
        index=index,
    )


def engine_result():
    price_data = prices()

    return run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=EngineConfig(
            research=ResearchConfig(
                volatility_window=10,
                trend_window=20,
                momentum_lookback=10,
                transaction_cost_bps=5.0,
            ),
            benchmark_name="synthetic",
            experiment_name="artifact-test",
        ),
    )


def test_experiment_directory(tmp_path):
    result = engine_result()

    path = experiment_directory(
        root=tmp_path,
        result=result,
    )

    assert path == (tmp_path / result.experiment_id)


def test_experiment_directory_requires_result(
    tmp_path,
):
    with pytest.raises(
        TypeError,
        match="EngineResult",
    ):
        experiment_directory(
            root=tmp_path,
            result="bad",
        )


def test_persist_engine_result(tmp_path):
    result = engine_result()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    assert directory.exists()
    assert directory.is_dir()

    expected = {
        "metadata.json",
        "result.json",
        "report.json",
        "summary.json",
        "manifest.json",
    }

    assert {path.name for path in directory.iterdir()} == expected


def test_persisted_manifest_contains_identity(
    tmp_path,
):
    result = engine_result()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    manifest = load_manifest(directory)

    assert manifest["experiment_id"] == result.experiment_id

    assert manifest["benchmark_name"] == "synthetic"

    assert manifest["experiment_name"] == "artifact-test"


def test_persisted_json_is_readable(
    tmp_path,
):
    result = engine_result()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    for filename in (
        "metadata.json",
        "result.json",
        "report.json",
        "summary.json",
        "manifest.json",
    ):
        payload = json.loads((directory / filename).read_text(encoding="utf-8"))

        assert isinstance(
            payload,
            dict,
        )


def test_artifact_verification_passes(
    tmp_path,
):
    result = engine_result()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    assert verify_experiment_artifacts(directory)


def test_artifact_verification_detects_tampering(
    tmp_path,
):
    result = engine_result()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    result_path = directory / "result.json"

    result_path.write_text(
        "{}",
        encoding="utf-8",
    )

    assert not verify_experiment_artifacts(directory)


def test_artifact_verification_detects_missing_file(
    tmp_path,
):
    result = engine_result()

    directory = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    (directory / "report.json").unlink()

    assert not verify_experiment_artifacts(directory)


def test_persist_rejects_existing_directory(
    tmp_path,
):
    result = engine_result()

    persist_engine_result(
        root=tmp_path,
        result=result,
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        persist_engine_result(
            root=tmp_path,
            result=result,
        )


def test_persist_overwrite_supported(
    tmp_path,
):
    result = engine_result()

    first = persist_engine_result(
        root=tmp_path,
        result=result,
    )

    second = persist_engine_result(
        root=tmp_path,
        result=result,
        overwrite=True,
    )

    assert first == second

    assert verify_experiment_artifacts(second)


def test_overwrite_requires_bool(
    tmp_path,
):
    with pytest.raises(
        TypeError,
        match="bool",
    ):
        persist_engine_result(
            root=tmp_path,
            result=engine_result(),
            overwrite=1,
        )


def test_persist_requires_result(
    tmp_path,
):
    with pytest.raises(
        TypeError,
        match="EngineResult",
    ):
        persist_engine_result(
            root=tmp_path,
            result="bad",
        )


def test_load_manifest_missing_directory(
    tmp_path,
):
    with pytest.raises(
        FileNotFoundError,
        match="does not exist",
    ):
        load_manifest(tmp_path / "missing")


def test_load_manifest_requires_directory(
    tmp_path,
):
    file_path = tmp_path / "file.txt"

    file_path.write_text(
        "x",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="directory",
    ):
        load_manifest(file_path)


def test_load_manifest_missing_manifest(
    tmp_path,
):
    directory = tmp_path / "experiment"

    directory.mkdir()

    with pytest.raises(
        FileNotFoundError,
        match="manifest",
    ):
        load_manifest(directory)


def test_invalid_manifest_json_rejected(
    tmp_path,
):
    directory = tmp_path / "experiment"

    directory.mkdir()

    (directory / "manifest.json").write_text(
        "{bad json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="valid JSON",
    ):
        load_manifest(directory)


def test_manifest_must_be_object(
    tmp_path,
):
    directory = tmp_path / "experiment"

    directory.mkdir()

    (directory / "manifest.json").write_text(
        "[]",
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="JSON object",
    ):
        load_manifest(directory)


def test_manifest_requires_files_section(
    tmp_path,
):
    directory = tmp_path / "experiment"

    directory.mkdir()

    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "x",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="files section",
    ):
        verify_experiment_artifacts(directory)


def test_manifest_requires_complete_file_set(
    tmp_path,
):
    directory = tmp_path / "experiment"

    directory.mkdir()

    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "files": {
                    "result.json": "abc",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="incomplete",
    ):
        verify_experiment_artifacts(directory)


def test_manifest_checksum_requires_string(
    tmp_path,
):
    directory = tmp_path / "experiment"

    directory.mkdir()

    files = {
        "metadata.json": 1,
        "result.json": "x",
        "report.json": "x",
        "summary.json": "x",
    }

    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "files": files,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="checksum",
    ):
        verify_experiment_artifacts(directory)
