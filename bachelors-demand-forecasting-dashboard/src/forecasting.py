"""Forecasting methods and accuracy metrics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing


MIN_OBSERVATIONS = 5


@dataclass(frozen=True)
class ForecastResult:
    """Container for forecast outputs and evaluation metrics."""

    method: str
    test_forecast: pd.DataFrame
    future_forecast: pd.DataFrame
    mae: float | None
    mape: float | None
    warnings: list[str]


def calculate_mape(actual: pd.Series | np.ndarray, predicted: pd.Series | np.ndarray) -> float:
    """Calculate MAPE while ignoring zero actual values.

    Returns NaN if all actual values are zero or invalid.
    """
    actual_arr = np.asarray(actual, dtype=float)
    predicted_arr = np.asarray(predicted, dtype=float)
    valid_mask = np.isfinite(actual_arr) & np.isfinite(predicted_arr) & (actual_arr != 0)
    if not valid_mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual_arr[valid_mask] - predicted_arr[valid_mask]) / actual_arr[valid_mask])) * 100)


def chronological_train_test_split(
    series: pd.Series,
    train_ratio: float = 0.8,
) -> tuple[pd.Series, pd.Series]:
    """Split a time series chronologically without shuffling."""
    if len(series) < 2:
        raise ValueError("At least two observations are required for train/test splitting.")

    split_index = int(np.floor(len(series) * train_ratio))
    split_index = min(max(split_index, 1), len(series) - 1)
    return series.iloc[:split_index], series.iloc[split_index:]


def run_moving_average_forecast(
    aggregated_df: pd.DataFrame,
    value_col: str = "revenue",
    date_col: str = "date",
    window: int = 7,
    horizon: int = 7,
    frequency: str = "Daily",
) -> ForecastResult:
    """Forecast revenue using a walk-forward moving average."""
    method = f"Moving Average ({window})"
    warnings: list[str] = []
    series, prep_warnings = prepare_time_series(aggregated_df, date_col, value_col, frequency)
    warnings.extend(prep_warnings)

    if len(series) < MIN_OBSERVATIONS:
        warnings.append("Too few observations for forecasting. At least five periods are required.")
        return _empty_result(method, warnings)

    train, test = chronological_train_test_split(series)
    window = max(1, int(window))
    history = train.astype(float).tolist()
    predictions: list[float] = []

    for actual_value in test.astype(float):
        prediction = float(np.mean(history[-window:]))
        predictions.append(prediction)
        history.append(float(actual_value))

    test_forecast = _build_test_forecast(test.index, test.to_numpy(), predictions, method)
    future_values = _recursive_moving_average(series.astype(float).tolist(), window, horizon)
    future_forecast = _build_future_forecast(
        make_future_index(series.index[-1], horizon, frequency),
        future_values,
        method,
    )

    return ForecastResult(
        method=method,
        test_forecast=test_forecast,
        future_forecast=future_forecast,
        mae=float(mean_absolute_error(test, predictions)),
        mape=calculate_mape(test, predictions),
        warnings=warnings,
    )


def run_exponential_smoothing_forecast(
    aggregated_df: pd.DataFrame,
    value_col: str = "revenue",
    date_col: str = "date",
    horizon: int = 7,
    frequency: str = "Daily",
    use_trend: bool = True,
    seasonal_periods: int | None = None,
) -> ForecastResult:
    """Forecast revenue using statsmodels Exponential Smoothing."""
    method = "Exponential Smoothing"
    warnings: list[str] = []
    series, prep_warnings = prepare_time_series(aggregated_df, date_col, value_col, frequency)
    warnings.extend(prep_warnings)

    if len(series) < MIN_OBSERVATIONS:
        warnings.append("Too few observations for Exponential Smoothing. At least five periods are required.")
        return _empty_result(method, warnings)

    train, test = chronological_train_test_split(series)
    trend = "add" if use_trend and len(train) >= 4 else None
    seasonal = None
    if seasonal_periods:
        if len(train) >= seasonal_periods * 2:
            seasonal = "add"
        else:
            warnings.append(
                "Not enough training observations for seasonal Exponential Smoothing; seasonality was disabled."
            )

    try:
        fitted = _fit_exponential_smoothing(train, trend, seasonal, seasonal_periods)
        test_predictions = np.asarray(fitted.forecast(len(test)), dtype=float)
    except Exception as exc:
        warnings.append(f"Exponential Smoothing could not be fitted: {exc}")
        return _empty_result(method, warnings)

    try:
        full_fitted = _fit_exponential_smoothing(series, trend, seasonal, seasonal_periods)
        future_predictions = np.asarray(full_fitted.forecast(horizon), dtype=float)
    except Exception as exc:
        warnings.append(f"Future Exponential Smoothing forecast failed: {exc}")
        future_predictions = np.asarray([], dtype=float)

    test_forecast = _build_test_forecast(test.index, test.to_numpy(), test_predictions, method)
    future_forecast = _build_future_forecast(
        make_future_index(series.index[-1], len(future_predictions), frequency),
        future_predictions,
        method,
    )

    return ForecastResult(
        method=method,
        test_forecast=test_forecast,
        future_forecast=future_forecast,
        mae=float(mean_absolute_error(test, test_predictions)),
        mape=calculate_mape(test, test_predictions),
        warnings=warnings,
    )


def prepare_time_series(
    aggregated_df: pd.DataFrame,
    date_col: str = "date",
    value_col: str = "revenue",
    frequency: str = "Daily",
) -> tuple[pd.Series, list[str]]:
    """Return a regular time series, filling missing periods with zero revenue."""
    warnings: list[str] = []
    if aggregated_df.empty:
        return pd.Series(dtype=float), ["Dataset is empty after filtering or aggregation."]
    if date_col not in aggregated_df.columns or value_col not in aggregated_df.columns:
        return pd.Series(dtype=float), [f"Dataset must contain `{date_col}` and `{value_col}` columns."]

    working = aggregated_df[[date_col, value_col]].copy()
    working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
    working[value_col] = pd.to_numeric(working[value_col], errors="coerce")
    working = working.dropna(subset=[date_col, value_col])
    if working.empty:
        return pd.Series(dtype=float), ["No valid dated revenue observations are available."]

    working = working.groupby(date_col, as_index=True)[value_col].sum().sort_index()
    pandas_frequency = frequency_to_pandas(frequency)
    full_index = pd.date_range(working.index.min(), working.index.max(), freq=pandas_frequency)
    missing_period_count = len(full_index.difference(working.index))
    if missing_period_count > 0:
        warnings.append(f"{missing_period_count} missing period(s) were filled with zero revenue for forecasting.")

    regular_series = working.reindex(full_index, fill_value=0).astype(float)
    regular_series.index.name = date_col
    return regular_series, warnings


def frequency_to_pandas(frequency: str) -> str:
    """Map dashboard frequency labels to pandas frequencies."""
    frequency_normalized = frequency.lower()
    if frequency_normalized == "daily":
        return "D"
    if frequency_normalized == "weekly":
        return "W-MON"
    if frequency_normalized == "monthly":
        return "MS"
    raise ValueError("frequency must be one of: Daily, Weekly, Monthly")


def make_future_index(last_date: pd.Timestamp, horizon: int, frequency: str) -> pd.DatetimeIndex:
    """Create future period labels after the last observed date."""
    if horizon <= 0:
        return pd.DatetimeIndex([])

    pandas_frequency = frequency_to_pandas(frequency)
    start = pd.Timestamp(last_date) + pd.tseries.frequencies.to_offset(pandas_frequency)
    return pd.date_range(start=start, periods=horizon, freq=pandas_frequency)


def _fit_exponential_smoothing(
    series: pd.Series,
    trend: str | None,
    seasonal: str | None,
    seasonal_periods: int | None,
):
    return ExponentialSmoothing(
        series,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods if seasonal else None,
        initialization_method="estimated",
    ).fit(optimized=True)


def _recursive_moving_average(history: list[float], window: int, horizon: int) -> list[float]:
    values = list(history)
    predictions: list[float] = []
    for _ in range(max(0, int(horizon))):
        prediction = float(np.mean(values[-window:]))
        predictions.append(prediction)
        values.append(prediction)
    return predictions


def _build_test_forecast(
    dates: pd.Index,
    actual: np.ndarray,
    predicted: list[float] | np.ndarray,
    method: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "actual": np.asarray(actual, dtype=float),
            "predicted": np.asarray(predicted, dtype=float),
            "method": method,
        }
    )


def _build_future_forecast(
    dates: pd.Index,
    predicted: list[float] | np.ndarray,
    method: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "predicted": np.asarray(predicted, dtype=float),
            "method": method,
        }
    )


def _empty_result(method: str, warnings: list[str]) -> ForecastResult:
    return ForecastResult(
        method=method,
        test_forecast=pd.DataFrame(columns=["date", "actual", "predicted", "method"]),
        future_forecast=pd.DataFrame(columns=["date", "predicted", "method"]),
        mae=None,
        mape=None,
        warnings=warnings,
    )

