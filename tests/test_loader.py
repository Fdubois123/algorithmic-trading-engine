import pandas as pd
import pytest

from trading_engine.data.loader import MarketDataLoader


@pytest.fixture
def valid_csv(tmp_path):
    file_path = tmp_path / "market_data.csv"

    file_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01,100,105,98,103,1000\n"
        "2026-01-02,103,108,101,106,1200\n"
        "2026-01-03,106,110,104,109,1500\n",
        encoding="utf-8",
    )

    return file_path


def test_load_valid_csv(valid_csv):
    data = MarketDataLoader.from_csv(valid_csv)

    assert isinstance(data, pd.DataFrame)
    assert isinstance(data.index, pd.DatetimeIndex)
    assert len(data) == 3


def test_columns_are_normalized(tmp_path):
    file_path = tmp_path / "market_data.csv"

    file_path.write_text(
        "Timestamp,Open,HIGH,Low,Close,Volume\n"
        "2026-01-01,100,105,98,103,1000\n",
        encoding="utf-8",
    )

    data = MarketDataLoader.from_csv(file_path)

    assert list(data.columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]


def test_unsorted_timestamps_are_sorted(tmp_path):
    file_path = tmp_path / "market_data.csv"

    file_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-03,106,110,104,109,1500\n"
        "2026-01-01,100,105,98,103,1000\n"
        "2026-01-02,103,108,101,106,1200\n",
        encoding="utf-8",
    )

    data = MarketDataLoader.from_csv(file_path)

    assert data.index.is_monotonic_increasing


def test_missing_file_raises_error(tmp_path):
    file_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="not found"):
        MarketDataLoader.from_csv(file_path)


def test_missing_timestamp_raises_error(tmp_path):
    file_path = tmp_path / "market_data.csv"

    file_path.write_text(
        "open,high,low,close,volume\n"
        "100,105,98,103,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="timestamp"):
        MarketDataLoader.from_csv(file_path)


def test_duplicate_timestamps_raise_error(tmp_path):
    file_path = tmp_path / "market_data.csv"

    file_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01,100,105,98,103,1000\n"
        "2026-01-01,103,108,101,106,1200\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate timestamps"):
        MarketDataLoader.from_csv(file_path)


def test_invalid_timestamp_raises_error(tmp_path):
    file_path = tmp_path / "market_data.csv"

    file_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "not-a-date,100,105,98,103,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid timestamps"):
        MarketDataLoader.from_csv(file_path)