import numpy as np
import pandas as pd

from src.forecasting import (
    calculate_mape,
    chronological_train_test_split,
    run_exponential_smoothing_forecast,
    run_linear_regression_forecast,
    run_moving_average_forecast,
)


def test_chronological_train_test_split_preserves_order():
    series = pd.Series(range(10), index=pd.date_range("2024-01-01", periods=10))

    train, test = chronological_train_test_split(series)

    assert train.tolist() == list(range(8))
    assert test.tolist() == [8, 9]


def test_mape_ignores_zero_actual_values():
    actual = np.array([0, 100, 200])
    predicted = np.array([50, 110, 180])

    mape = calculate_mape(actual, predicted)

    assert round(mape, 2) == 10.0


def test_mape_returns_nan_when_all_actual_values_are_zero():
    actual = np.array([0, 0])
    predicted = np.array([10, 20])

    assert np.isnan(calculate_mape(actual, predicted))


def test_moving_average_forecast_output_shape():
    aggregated_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=20, freq="D"),
            "revenue": np.arange(100, 120),
        }
    )

    result = run_moving_average_forecast(aggregated_df, window=3, horizon=7)

    assert len(result.test_forecast) == 4
    assert len(result.future_forecast) == 7
    assert {"date", "actual", "predicted", "method"}.issubset(result.test_forecast.columns)


def test_moving_average_forecast_handles_too_few_observations():
    aggregated_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3, freq="D"),
            "revenue": [100, 110, 120],
        }
    )

    result = run_moving_average_forecast(aggregated_df, window=2, horizon=7)

    assert result.test_forecast.empty
    assert result.future_forecast.empty
    assert result.warnings


def test_exponential_smoothing_forecast_can_include_prediction_intervals():
    aggregated_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=40, freq="D"),
            "revenue": np.linspace(100, 180, 40),
        }
    )

    result = run_exponential_smoothing_forecast(
        aggregated_df,
        horizon=7,
        confidence_level=0.95,
    )

    assert {"lower_bound", "upper_bound"}.issubset(result.future_forecast.columns)
    assert result.confidence_level == 0.95


def test_linear_regression_forecast_returns_model_details_and_intervals():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    revenue = np.linspace(100, 160, 60) + np.where(dates.dayofweek >= 5, 12, 0)
    promotion_active = (dates.dayofweek == 4).astype(int)

    aggregated_df = pd.DataFrame(
        {
            "date": dates,
            "revenue": revenue,
            "promotion_active": promotion_active,
        }
    )

    result = run_linear_regression_forecast(
        aggregated_df,
        horizon=7,
        promotion_col="promotion_active",
        confidence_level=0.9,
    )

    assert len(result.test_forecast) == 12
    assert len(result.future_forecast) == 7
    assert {"lower_bound", "upper_bound"}.issubset(result.test_forecast.columns)
    assert result.model_details is not None and not result.model_details.empty
    assert result.features_used is not None and "promotion_active" in result.features_used

