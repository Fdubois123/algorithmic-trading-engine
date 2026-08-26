import json

import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    ResearchConfig,
    ResearchResult,
    build_experiment_metadata,
    build_research_report,
    dataframe_to_records,
    export_research_bundle,
    research_report_to_dict,
    research_result_to_dict,
    series_to_records,
)


def research_result():
    index = pd.date_range(
        "2026-01-01",
        periods=3,
        freq="D",
    )

    returns = pd.Series(
        [
            0.0,
            0.01,
            -0.005,
        ],
        index=index,
    )

    weights = pd.DataFrame(
        {
            "trend": [
                0.0,
                0.5,
                0.5,
            ],
            "momentum": [
                0.0,
                0.5,
                0.5,
            ],
        },
        index=index,
    )

    return ResearchResult(
        equity_curve=(1.0 + returns).cumprod(),
        returns=returns,
        gross_returns=returns,
        regime_frame=pd.DataFrame(
            {
                "market_regime": [
                    "bull",
                    "bull",
                    "bear",
                ]
            },
            index=index,
        ),
        target_weights=weights.copy(),
        applied_weights=weights,
        turnover=pd.Series(
            [
                0.0,
                0.5,
                0.0,
            ],
            index=index,
        ),
        transaction_costs=pd.Series(
            [
                0.0,
                0.001,
                0.0,
            ],
            index=index,
        ),
    )


def strategy_returns():
    index = research_result().returns.index

    return pd.DataFrame(
        {
            "trend": [
                0.01,
                0.02,
                -0.01,
            ],
            "momentum": [
                0.02,
                0.00,
                -0.01,
            ],
        },
        index=index,
    )


def test_series_to_records():
    value = pd.Series(
        [
            1.0,
            2.0,
        ],
        index=pd.date_range(
            "2026-01-01",
            periods=2,
            freq="D",
        ),
    )

    result = series_to_records(value)

    assert len(result) == 2
    assert "index" in result[0]
    assert "value" in result[0]


def test_series_to_records_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        series_to_records([])


def test_dataframe_to_records():
    frame = pd.DataFrame(
        {
            "value": [
                1,
                2,
            ]
        }
    )

    result = dataframe_to_records(frame)

    assert len(result) == 2
    assert result[0]["value"] == 1


def test_dataframe_to_records_requires_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        dataframe_to_records([])


def test_research_result_to_dict():
    result = research_result_to_dict(research_result())

    assert result["observations"] == 3

    assert "equity_curve" in result
    assert "regime_frame" in result


def test_research_result_to_dict_requires_result():
    with pytest.raises(
        TypeError,
        match="ResearchResult",
    ):
        research_result_to_dict("bad")


def test_research_report_to_dict():
    result = research_result()

    report = build_research_report(
        result=result,
        strategy_returns=strategy_returns(),
        rolling_window=2,
    )

    payload = research_report_to_dict(report)

    assert "overview" in payload
    assert "drawdown" in payload
    assert "costs" in payload


def test_research_report_to_dict_requires_report():
    with pytest.raises(
        TypeError,
        match="ResearchReport",
    ):
        research_report_to_dict("bad")


def test_export_research_bundle(tmp_path):
    result = research_result()

    report = build_research_report(
        result=result,
        strategy_returns=strategy_returns(),
        rolling_window=2,
    )

    metadata = build_experiment_metadata(
        config=ResearchConfig(),
        observations=result.observations,
        strategy_count=2,
    )

    destination = tmp_path / "research.json"

    written = export_research_bundle(
        path=destination,
        metadata=metadata,
        result=result,
        report=report,
    )

    assert written == destination
    assert written.exists()

    payload = json.loads(written.read_text(encoding="utf-8"))

    assert "metadata" in payload
    assert "result" in payload
    assert "report" in payload


def test_export_without_report(tmp_path):
    result = research_result()

    metadata = build_experiment_metadata(
        config=ResearchConfig(),
        observations=result.observations,
        strategy_count=2,
    )

    destination = tmp_path / "research.json"

    export_research_bundle(
        path=destination,
        metadata=metadata,
        result=result,
    )

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert "report" not in payload


def test_export_requires_metadata(tmp_path):
    with pytest.raises(
        TypeError,
        match="ExperimentMetadata",
    ):
        export_research_bundle(
            path=(tmp_path / "research.json"),
            metadata="bad",
            result=research_result(),
        )


def test_export_requires_json_suffix(tmp_path):
    metadata = build_experiment_metadata(
        config=ResearchConfig(),
        observations=3,
        strategy_count=2,
    )

    with pytest.raises(
        ValueError,
        match=".json",
    ):
        export_research_bundle(
            path=(tmp_path / "research.txt"),
            metadata=metadata,
            result=research_result(),
        )


def test_export_rejects_directory(tmp_path):
    metadata = build_experiment_metadata(
        config=ResearchConfig(),
        observations=3,
        strategy_count=2,
    )

    with pytest.raises(
        ValueError,
        match="file",
    ):
        export_research_bundle(
            path=tmp_path,
            metadata=metadata,
            result=research_result(),
        )


def test_serialization_handles_numpy_and_missing():
    frame = pd.DataFrame(
        {
            "value": [
                np.float64(1.5),
                pd.NA,
            ]
        }
    )

    result = dataframe_to_records(frame)

    assert result[0]["value"] == 1.5

    assert result[1]["value"] is None
