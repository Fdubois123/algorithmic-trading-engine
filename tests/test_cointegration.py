import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb.cointegration import (
    EngleGrangerDiagnostic,
    StationarityDiagnostic,
    engle_granger_diagnostic,
    residual_adf_statistic,
)


def series(
    values,
):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def stationary_residuals(
    observations: int = 200,
) -> pd.Series:
    values = [1.0]

    for index in range(observations - 1):
        shock = 0.1 * np.sin(index)

        values.append(0.5 * values[-1] + shock)

    return series(values)


def test_residual_adf_returns_result():
    result = residual_adf_statistic(stationary_residuals())

    assert isinstance(
        result,
        StationarityDiagnostic,
    )

    assert np.isfinite(result.lagged_coefficient)

    assert result.observations == 200


def test_stationary_residual_is_identified():
    result = residual_adf_statistic(
        stationary_residuals(),
        critical_value=-2.0,
    )

    assert result.stationary


def test_custom_critical_value_is_recorded():
    result = residual_adf_statistic(
        stationary_residuals(),
        critical_value=-2.5,
    )

    assert result.critical_value == pytest.approx(-2.5)


def test_residuals_must_be_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        residual_adf_statistic([1, 2, 3, 4, 5])


def test_empty_residuals_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        residual_adf_statistic(pd.Series(dtype=float))


def test_short_residual_series_rejected():
    with pytest.raises(
        ValueError,
        match="at least 5",
    ):
        residual_adf_statistic(series([1, 2, 3, 4]))


def test_non_finite_residual_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        residual_adf_statistic(
            series(
                [
                    1,
                    2,
                    np.inf,
                    3,
                    4,
                ]
            )
        )


def test_constant_residual_rejected():
    with pytest.raises(
        ValueError,
        match="non-zero",
    ):
        residual_adf_statistic(series([1, 1, 1, 1, 1, 1]))


@pytest.mark.parametrize(
    "critical",
    [
        True,
        "3",
    ],
)
def test_critical_value_must_be_numeric(
    critical,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        residual_adf_statistic(
            stationary_residuals(),
            critical_value=critical,
        )


def test_non_finite_critical_value_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        residual_adf_statistic(
            stationary_residuals(),
            critical_value=np.inf,
        )


def test_engle_granger_diagnostic():
    observations = 200

    x = np.linspace(
        50,
        100,
        observations,
    )

    residual = stationary_residuals(observations).to_numpy()

    dependent = series(5.0 + 2.0 * x + residual)

    independent = series(x)

    result = engle_granger_diagnostic(
        dependent,
        independent,
        critical_value=-2.0,
    )

    assert isinstance(
        result,
        EngleGrangerDiagnostic,
    )

    assert result.hedge.beta == pytest.approx(
        2.0,
        abs=0.1,
    )

    assert result.cointegrated
