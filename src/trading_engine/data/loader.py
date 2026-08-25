from __future__ import annotations

from pathlib import Path

import pandas as pd

from trading_engine.data.validator import MarketDataValidator


class MarketDataLoader:
    """Load and standardize OHLCV market data."""

    @staticmethod
    def from_csv(file_path: str | Path) -> pd.DataFrame:
        """Load OHLCV data from a CSV file.

        The CSV must contain a timestamp column and the standard
        OHLCV fields: open, high, low, close, and volume.

        Args:
            file_path: Path to the CSV file.

        Returns:
            A validated DataFrame indexed by timestamp.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            ValueError: If required data is missing or invalid.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Market data file not found: {path}")

        data = pd.read_csv(path)

        # Normalize column names.
        data.columns = [str(column).strip().lower() for column in data.columns]

        if "timestamp" not in data.columns:
            raise ValueError("CSV must contain a 'timestamp' column.")

        try:
            data["timestamp"] = pd.to_datetime(
                data["timestamp"],
                errors="raise",
            )
        except (ValueError, TypeError) as exc:
            raise ValueError("CSV contains invalid timestamps.") from exc

        if data["timestamp"].duplicated().any():
            raise ValueError("CSV contains duplicate timestamps.")

        data = data.sort_values("timestamp")
        data = data.set_index("timestamp")

        MarketDataValidator.validate(data)

        return data