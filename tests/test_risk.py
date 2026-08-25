import numpy as np
import pandas as pd
import pytest

from trading_engine.risk.tail import (
    historical_cvar,
    historical_var,
)


def test_historical_var_is_correct():
    returns = pd.Series([-0.10, -0.05, 0.00, 0.05, 0.10])

    result = historical_var(
        returns,
        confidence_level=0.80,
    )

    assert result >= 0


def test_historical_cvar_is_at_least_var():
    returns = pd.Series([-0.10, -0.08, -0.05, 0.01, 0.02, 0.03])

    var = historical_var(
        returns,
        confidence_level=0.80,
    )

    cvar = historical_cvar(
        returns,
        confidence_level=0.80,
    )

    assert cvar >= var


def test_positive_returns_have_zero_var():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = historical_var(
        returns,
        confidence_level=0.95,
    )

    assert result == pytest.approx(0.0)


def test_positive_returns_have_zero_cvar():
    returns = pd.Series([0.01, 0.02, 0.03])

    result = historical_cvar(
        returns,
        confidence_level=0.95,
    )

    assert result == pytest.approx(0.0)


@pytest.mark.parametrize(
    "confidence",
    [0, 1, -0.1, 1.1],
)
def test_invalid_confidence_level_raises_error(confidence):
    returns = pd.Series([0.01, -0.01])

    with pytest.raises(ValueError, match="between 0 and 1"):
        historical_var(
            returns,
            confidence_level=confidence,
        )


def test_non_numeric_confidence_level_raises_error():
    returns = pd.Series([0.01, -0.01])

    with pytest.raises(TypeError, match="numeric"):
        historical_var(
            returns,
            confidence_level="0.95",
        )


def test_non_finite_confidence_level_raises_error():
    returns = pd.Series([0.01, -0.01])

    with pytest.raises(ValueError, match="finite"):
        historical_var(
            returns,
            confidence_level=np.inf,
        )


def test_var_rejects_no_valid_observations():
    returns = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        historical_var(returns)


def test_cvar_rejects_no_valid_observations():
    returns = pd.Series([np.nan, np.nan])

    with pytest.raises(ValueError, match="no valid observations"):
        historical_cvar(returns)


@pytest.mark.parametrize(
    "confidence",
    [0, 1, -0.5, 1.5],
)
def test_cvar_rejects_out_of_range_confidence(confidence):
    returns = pd.Series([-0.02, 0.01])

    with pytest.raises(ValueError, match="between 0 and 1"):
        historical_cvar(
            returns,
            confidence_level=confidence,
        )


def test_cvar_rejects_non_numeric_confidence():
    returns = pd.Series([-0.02, 0.01])

    with pytest.raises(TypeError, match="numeric"):
        historical_cvar(
            returns,
            confidence_level="0.95",
        )


def test_cvar_rejects_non_finite_confidence():
    returns = pd.Series([-0.02, 0.01])

    with pytest.raises(ValueError, match="finite"):
        historical_cvar(
            returns,
            confidence_level=np.nan,
        )
