from __future__ import annotations

from typing import ClassVar

import pandas as pd


class MarketDataValidator:
    """Validate OHLCV market data used by the trading engine."""

    REQUIRED_COLUMNS: ClassVar[frozenset[str]] = frozenset(
    {"open", "high", "low", "close", "volume"}
)

    @classmethod
    def validate(cls, data: pd.DataFrame) -> None:
        """Validate a market-data DataFrame.

        Raises:
            TypeError: If data is not a pandas DataFrame.
            ValueError: If data is empty, missing required columns,
                contains null values, or contains invalid OHLC prices.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Market data must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Market data cannot be empty.")

        missing_columns = cls.REQUIRED_COLUMNS - set(data.columns)

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required columns: {missing}")

        if data[list(cls.REQUIRED_COLUMNS)].isnull().any().any():
            raise ValueError("Market data contains missing values.")

        invalid_high = data["high"] < data[["open", "close"]].max(axis=1)

        if invalid_high.any():
            raise ValueError("High price is inconsistent with OHLC values.")

        invalid_low = data["low"] > data[["open", "close"]].min(axis=1)

        if invalid_low.any():
            raise ValueError("Low price is inconsistent with OHLC values.")

        if (data["volume"] < 0).any():
            raise ValueError("Volume cannot be negative.")