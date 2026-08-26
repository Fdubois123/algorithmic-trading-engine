import pandas as pd
import pytest

from trading_engine.regime import (
    RegimeTransition,
    extract_regime_transitions,
    regime_persistence,
    regime_transition_flags,
)


def regimes():
    return pd.Series(
        [
            pd.NA,
            "low_vol_bull",
            "low_vol_bull",
            "normal_vol_bull",
            "normal_vol_bull",
            "high_vol_bear",
        ],
        index=pd.date_range(
            "2026-01-01",
            periods=6,
            freq="D",
        ),
        dtype="object",
    )


def test_transition_flags():
    result = regime_transition_flags(regimes())

    assert not result.iloc[1]
    assert not result.iloc[2]
    assert result.iloc[3]
    assert result.iloc[5]


def test_regime_persistence():
    result = regime_persistence(regimes())

    assert result.iloc[0] == 0
    assert result.iloc[1] == 1
    assert result.iloc[2] == 2
    assert result.iloc[3] == 1
    assert result.iloc[4] == 2
    assert result.iloc[5] == 1


def test_extract_transitions():
    result = extract_regime_transitions(regimes())

    assert len(result) == 2

    assert isinstance(
        result[0],
        RegimeTransition,
    )

    assert result[0].previous == "low_vol_bull"

    assert result[0].current == "normal_vol_bull"


def test_transition_series_required():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        regime_transition_flags([])


def test_empty_transition_series_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        regime_persistence(pd.Series(dtype="object"))


def test_missing_value_resets_persistence():
    data = pd.Series(
        [
            "bull",
            "bull",
            pd.NA,
            "bull",
        ],
        dtype="object",
    )

    result = regime_persistence(data)

    assert result.tolist() == [
        1,
        2,
        0,
        1,
    ]
