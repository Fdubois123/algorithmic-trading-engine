import pandas as pd
import pytest

from trading_engine.data.validator import MarketDataValidator


@pytest.fixture
def valid_market_data():
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [103.0, 104.0, 105.0],
            "low": [99.0, 100.0, 101.0],
            "close": [102.0, 103.0, 104.0],
            "volume": [1000, 1200, 1100],
        }
    )


def test_valid_market_data_passes(valid_market_data):
    MarketDataValidator.validate(valid_market_data)


def test_missing_column_raises_error(valid_market_data):
    data = valid_market_data.drop(columns=["volume"])

    with pytest.raises(ValueError, match="Missing required columns"):
        MarketDataValidator.validate(data)


def test_empty_dataframe_raises_error():
    with pytest.raises(ValueError, match="cannot be empty"):
        MarketDataValidator.validate(pd.DataFrame())


def test_null_values_raise_error(valid_market_data):
    data = valid_market_data.copy()
    data.loc[1, "close"] = None

    with pytest.raises(ValueError, match="missing values"):
        MarketDataValidator.validate(data)


def test_invalid_high_raises_error(valid_market_data):
    data = valid_market_data.copy()
    data.loc[0, "high"] = 98.0

    with pytest.raises(ValueError, match="High price"):
        MarketDataValidator.validate(data)


def test_invalid_low_raises_error(valid_market_data):
    data = valid_market_data.copy()
    data.loc[0, "low"] = 104.0

    with pytest.raises(ValueError, match="Low price"):
        MarketDataValidator.validate(data)


def test_negative_volume_raises_error(valid_market_data):
    data = valid_market_data.copy()
    data.loc[0, "volume"] = -100

    with pytest.raises(ValueError, match="Volume cannot be negative"):
        MarketDataValidator.validate(data)