import numpy as np
import pandas as pd
import pytest

from trading_engine.regime.allocation import (
    normalize_strategy_weights,
    regime_gross_exposure,
    validate_strategy_weights,
)
from trading_engine.regime.convergence import (
    run_adaptive_convergence,
)
from trading_engine.regime.drawdown import (
    classify_drawdown_regime,
    running_drawdown,
)
from trading_engine.regime.labels import (
    MarketRegime,
)
from trading_engine.regime.momentum import (
    classify_momentum_regime,
    rolling_momentum,
)


def prices(values):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def strategy_returns():
    return pd.DataFrame(
        {
            "trend": [0.01, 0.02, 0.01],
            "momentum": [0.02, 0.01, 0.01],
            "mean_reversion": [0.01, 0.01, 0.02],
            "volatility": [0.00, 0.01, -0.01],
            "stat_arb": [0.01, 0.01, 0.01],
        },
        index=pd.date_range(
            "2026-01-01",
            periods=3,
            freq="D",
        ),
    )


def regimes():
    return [
        MarketRegime.LOW_VOL_BULL,
        MarketRegime.NORMAL_VOL_BULL,
        MarketRegime.HIGH_VOL_BEAR,
    ]


# ---------------------------------------------------------------------------
# allocation.py
# ---------------------------------------------------------------------------


def test_strategy_name_must_be_string():
    with pytest.raises(
        TypeError,
        match="strings",
    ):
        validate_strategy_weights(
            {
                123: 1.0,
            }
        )


def test_empty_strategy_name_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        validate_strategy_weights(
            {
                "   ": 1.0,
            }
        )


def test_zero_total_strategy_weights_rejected():
    with pytest.raises(
        ValueError,
        match="positive total",
    ):
        validate_strategy_weights(
            {
                "trend": 0.0,
                "momentum": 0.0,
            }
        )


def test_zero_total_allowed_when_requested():
    result = validate_strategy_weights(
        {
            "trend": 0.0,
            "momentum": 0.0,
        },
        require_positive_total=False,
    )

    assert result == {
        "trend": 0.0,
        "momentum": 0.0,
    }


def test_normalize_rejects_zero_total():
    with pytest.raises(
        ValueError,
        match="positive total",
    ):
        normalize_strategy_weights(
            {
                "trend": 0.0,
            }
        )


def test_regime_gross_exposure_requires_enum():
    with pytest.raises(
        TypeError,
        match="MarketRegime",
    ):
        regime_gross_exposure(
            "low_vol_bull",
        )


@pytest.mark.parametrize(
    "confidence",
    [
        True,
        "1",
    ],
)
def test_regime_confidence_requires_numeric(
    confidence,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        regime_gross_exposure(
            MarketRegime.LOW_VOL_BULL,
            confidence=confidence,
        )


def test_regime_confidence_non_finite_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        regime_gross_exposure(
            MarketRegime.LOW_VOL_BULL,
            confidence=np.inf,
        )


def test_negative_regime_confidence_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        regime_gross_exposure(
            MarketRegime.LOW_VOL_BULL,
            confidence=-0.1,
        )


def test_zero_maximum_exposure_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        regime_gross_exposure(
            MarketRegime.LOW_VOL_BULL,
            maximum_exposure=0.0,
        )


# ---------------------------------------------------------------------------
# drawdown.py
# ---------------------------------------------------------------------------


def test_drawdown_prices_require_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        running_drawdown([100, 90])


def test_empty_drawdown_prices_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        running_drawdown(pd.Series(dtype=float))


def test_non_numeric_drawdown_prices_rejected():
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        running_drawdown(pd.Series(["a", "b"]))


def test_non_positive_drawdown_prices_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        running_drawdown(prices([100, 0]))


@pytest.mark.parametrize(
    "value",
    [
        True,
        "0",
    ],
)
def test_drawdown_value_requires_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        classify_drawdown_regime(value)


def test_non_finite_drawdown_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        classify_drawdown_regime(np.inf)


def test_non_negative_moderate_threshold_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        classify_drawdown_regime(
            -0.1,
            moderate_threshold=0.0,
        )


# ---------------------------------------------------------------------------
# momentum.py
# ---------------------------------------------------------------------------


def test_momentum_prices_require_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        rolling_momentum([100, 101])


def test_empty_momentum_prices_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        rolling_momentum(pd.Series(dtype=float))


def test_non_numeric_momentum_prices_rejected():
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        rolling_momentum(pd.Series(["a", "b"]))


def test_non_finite_momentum_prices_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        rolling_momentum(prices([100, np.inf]))


def test_non_positive_momentum_prices_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        rolling_momentum(prices([100, 0]))


@pytest.mark.parametrize(
    "value",
    [
        True,
        "0.1",
    ],
)
def test_momentum_value_requires_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        classify_momentum_regime(value)


def test_non_finite_momentum_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        classify_momentum_regime(np.inf)


# ---------------------------------------------------------------------------
# convergence.py
# ---------------------------------------------------------------------------


def test_duplicate_strategy_columns_rejected():
    frame = strategy_returns()

    frame.columns = [
        "trend",
        "trend",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="columns must be unique",
    ):
        run_adaptive_convergence(
            strategy_returns=frame,
            regimes=regimes(),
        )


def test_empty_strategy_column_name_rejected():
    frame = strategy_returns()

    frame.columns = [
        "",
        "momentum",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="non-empty strategy names",
    ):
        run_adaptive_convergence(
            strategy_returns=frame,
            regimes=regimes(),
        )


def test_non_string_strategy_column_rejected():
    frame = strategy_returns()

    frame.columns = [
        1,
        "momentum",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="non-empty strategy names",
    ):
        run_adaptive_convergence(
            strategy_returns=frame,
            regimes=regimes(),
        )


def test_confidence_string_rejected():
    frame = strategy_returns()

    with pytest.raises(
        TypeError,
        match="numeric sequence",
    ):
        run_adaptive_convergence(
            strategy_returns=frame,
            regimes=regimes(),
            confidence="1.0",
        )


def test_regimes_string_rejected():
    frame = strategy_returns()

    with pytest.raises(
        TypeError,
        match="sequence",
    ):
        run_adaptive_convergence(
            strategy_returns=frame,
            regimes="bull",
        )
